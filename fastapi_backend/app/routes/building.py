import logging
import time
from collections import defaultdict

import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query

from app.config import settings

router = APIRouter(prefix="/building", tags=["building"])
logger = logging.getLogger(__name__)

JUSO_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
JUSO_COORD_URL = "https://business.juso.go.kr/addrlink/addrCoordApi.do"
BLDRGST_BASE = "http://apis.data.go.kr/1613000/BldRgstHubService"
VWORLD_2D_DATA = "https://api.vworld.kr/req/data"
VWORLD_2D_LAYER = "LP_PA_CBND_BUBUN"
VWORLD_NED_ATTR = "https://api.vworld.kr/ned/data/getIndvdLandPriceAttr"
# VWORLD API는 등록된 서비스URL의 Referer 헤더가 필요
VWORLD_REFERER = "https://frontend-production-7e58.up.railway.app/"
_LAND_BBOX_DELTA = 0.0003  # ~30m

# ── 캐시: 주소 → 결과 (24h TTL, 최대 200개 항목) ──────────────────────────
_CACHE_TTL = 86400
_CACHE_MAX = 200
_cache: dict[str, tuple[float, dict]] = {}


def _cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < _CACHE_TTL:
        return entry[1]
    _cache.pop(key, None)
    return None


def _cache_set(key: str, value: dict) -> None:
    if len(_cache) >= _CACHE_MAX:
        # 가장 오래된 항목 제거
        oldest = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest]
    _cache[key] = (time.time(), value)


# ── Rate limiter: 건축물대장 외부 API 분당 최대 5회 ────────────────────────
_EXT_RATE_LIMIT = 5  # calls per minute
_ext_call_times: list[float] = []


def _check_rate_limit() -> None:
    now = time.time()
    _ext_call_times[:] = [t for t in _ext_call_times if now - t < 60]
    if len(_ext_call_times) >= _EXT_RATE_LIMIT:
        wait_sec = int(60 - (now - _ext_call_times[0])) + 1
        raise HTTPException(
            status_code=429,
            detail=f"건축물대장 API 호출 한도 초과 — {wait_sec}초 후 다시 시도하세요",
        )
    _ext_call_times.append(now)


async def require_admin(access_token: str | None = Cookie(None)) -> str:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return str(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _items_as_list(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, dict):
        return [raw]
    return raw


@router.get("/info")
async def get_building_info(
    address: str = Query(..., min_length=1),
    _: str = Depends(require_admin),
) -> dict:
    if not settings.JUSO_API_KEY or not settings.BUILDING_API_KEY:
        raise HTTPException(status_code=503, detail="건물 정보 API 키가 설정되지 않았습니다")

    cache_key = address.strip().lower()
    cached = _cache_get(cache_key)
    if cached:
        logger.info("Building cache hit: %s", address)
        return cached

    # 캐시 미스 시에만 외부 API 호출 — rate limit 체크
    _check_rate_limit()

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Step 1: Juso API — 주소 → admCd + 지번
        try:
            juso_resp = await client.get(
                JUSO_URL,
                params={
                    "confmKey": settings.JUSO_API_KEY,
                    "currentPage": 1,
                    "countPerPage": 1,
                    "keyword": address,
                    "resultType": "json",
                },
            )
            juso_resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Juso API error: %s", e)
            raise HTTPException(status_code=502, detail="주소 검색 API 오류")

        juso_data = juso_resp.json()
        error_code = juso_data.get("results", {}).get("common", {}).get("errorCode", "0")
        if error_code != "0":
            raise HTTPException(status_code=502, detail="주소 API 오류: " + error_code)

        juso_list = juso_data.get("results", {}).get("juso") or []
        if not juso_list:
            raise HTTPException(status_code=404, detail="주소를 찾을 수 없습니다")

        j = juso_list[0]
        adm_cd: str = j.get("admCd", "")
        if len(adm_cd) != 10:
            raise HTTPException(status_code=422, detail="행정구역코드 형식 오류")

        sigungu_cd = adm_cd[:5]
        bjdong_cd = adm_cd[5:]
        bun = str(j.get("lnbrMnnm") or "0").zfill(4)
        ji = str(j.get("lnbrSlno") or "0").zfill(4)

        # Step 1-b: Juso 좌표 API — 같은 key로 위경도 획득
        coord_lat: float | None = None
        coord_lon: float | None = None
        try:
            coord_resp = await client.get(
                JUSO_COORD_URL,
                params={
                    "confmKey": settings.JUSO_API_KEY,
                    "admCd": adm_cd,
                    "rnMgtSn": j.get("rnMgtSn", ""),
                    "udrtYn": j.get("udrtYn", "0"),
                    "buldMnnm": j.get("buldMnnm", 0),
                    "buldSlno": j.get("buldSlno", 0),
                    "resultType": "json",
                },
            )
            coord_data = coord_resp.json()
            coord_juso = coord_data.get("results", {}).get("juso") or []
            if coord_juso:
                coord_lat = float(coord_juso[0].get("lat") or 0) or None
                coord_lon = float(coord_juso[0].get("lon") or 0) or None
                logger.info("Juso coord OK: lat=%s lon=%s", coord_lat, coord_lon)
            else:
                logger.warning("Juso coord: 결과 없음 응답=%s", str(coord_data)[:200])
        except Exception as e:
            logger.warning("Juso coord API 실패: %s", e)

        bld_params = {
            "serviceKey": settings.BUILDING_API_KEY,
            "sigunguCd": sigungu_cd,
            "bjdongCd": bjdong_cd,
            "bun": bun,
            "ji": ji,
            "numOfRows": 10,
            "_type": "json",
        }

        # Step 2: 건축물대장 기본개요
        try:
            title_resp = await client.get(f"{BLDRGST_BASE}/getBrTitleInfo", params=bld_params)
            title_resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("BldRgst title API error: %s", e)
            raise HTTPException(status_code=502, detail="건축물대장 API 오류")

        title_raw = title_resp.json()
        title_items = _items_as_list(
            title_raw.get("response", {}).get("body", {}).get("items", {}).get("item")
        )

        if not title_items:
            result = {
                "found": False,
                "road_address": j.get("roadAddrPart1", address),
                "jibun_address": j.get("jibunAddr", ""),
            }
            _cache_set(cache_key, result)
            return result

        # 집합건물 표제부 우선, 없으면 첫 번째
        title = next(
            (t for t in title_items if "표제부" in (t.get("regstrKindCdNm") or "")),
            title_items[0],
        )

        # Step 3: 호수별 전유/공용 면적
        expo_params = {**bld_params, "numOfRows": 500}
        try:
            expo_resp = await client.get(
                f"{BLDRGST_BASE}/getBrExposPubuseAreaInfo", params=expo_params
            )
            expo_resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("BldRgst expo API error: %s", e)
            expo_items = []
        else:
            expo_raw = expo_resp.json()
            expo_items = _items_as_list(
                expo_raw.get("response", {}).get("body", {}).get("items", {}).get("item")
            )

        # 호수별 집계
        units: dict = defaultdict(
            lambda: {"floor": "", "purpose": "", "exclusive_sqm": 0.0, "common_sqm": 0.0}
        )
        for item in expo_items:
            ho = (item.get("hoNm") or "").strip()
            if not ho:
                continue
            units[ho]["floor"] = item.get("flrNoNm", "")
            units[ho]["purpose"] = item.get("mainPurpsCdNm", "")
            area = float(item.get("area") or 0)
            if item.get("exposPubuseGbCdNm") == "전유":
                units[ho]["exclusive_sqm"] += area
            else:
                units[ho]["common_sqm"] += area

        unit_list = [
            {
                "ho": ho,
                "floor": u["floor"],
                "purpose": u["purpose"],
                "exclusive_sqm": round(u["exclusive_sqm"], 2),
                "exclusive_py": round(u["exclusive_sqm"] / 3.3058, 1),
                "common_sqm": round(u["common_sqm"], 2),
            }
            for ho, u in sorted(units.items())
        ]

        result = {
            "found": True,
            "road_address": j.get("roadAddrPart1", ""),
            "jibun_address": j.get("jibunAddr", ""),
            "latitude": coord_lat,
            "longitude": coord_lon,
            "building_name": title.get("bldNm") or "",
            "total_floors": int(title.get("grndFlrCnt") or 0),
            "underground_floors": int(title.get("ugrndFlrCnt") or 0),
            "total_area_sqm": float(title.get("totArea") or 0),
            "total_units": int(title.get("hhldCnt") or len(unit_list)),
            "main_purpose": title.get("mainPurpsCdNm") or "",
            "units": unit_list,
        }
        _cache_set(cache_key, result)
        return result


@router.get("/land")
async def get_land_info(
    lat: float = Query(...),
    lon: float = Query(...),
    _: str = Depends(require_admin),
) -> dict:
    if not settings.VWORLD_API_KEY:
        raise HTTPException(status_code=503, detail="VWORLD API 키가 설정되지 않았습니다")

    import re

    d = _LAND_BBOX_DELTA
    geom_filter = f"BOX({lon - d},{lat - d},{lon + d},{lat + d})"
    headers = {"Referer": VWORLD_REFERER}

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Step 1: VWORLD 2D Data API → 필지 폴리곤 + 현재 공시지가 + PNU
        try:
            data_resp = await client.get(
                VWORLD_2D_DATA,
                headers=headers,
                params={
                    "service": "data",
                    "version": "2.0",
                    "request": "GetFeature",
                    "data": VWORLD_2D_LAYER,
                    "geomFilter": geom_filter,
                    "crs": "EPSG:4326",
                    "format": "json",
                    "size": 1,
                    "key": settings.VWORLD_API_KEY,
                },
            )
            data_resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("VWORLD 2D Data API 오류: %s", e)
            raise HTTPException(status_code=502, detail="VWORLD 데이터 API 오류")

        resp_json = data_resp.json()
        if resp_json.get("response", {}).get("status") != "OK":
            err = resp_json.get("response", {}).get("error", {})
            logger.warning("VWORLD 2D Data 오류 응답: %s", err)
            raise HTTPException(status_code=404, detail="해당 위치의 필지 정보가 없습니다")

        features = (
            resp_json.get("response", {})
            .get("result", {})
            .get("featureCollection", {})
            .get("features", [])
        )
        if not features:
            raise HTTPException(status_code=404, detail="해당 위치의 필지 정보가 없습니다")

        feature = features[0]
        props = feature.get("properties", {})
        pnu: str = str(props.get("pnu", "") or "")
        current_price = int(props.get("jiga", 0) or 0)
        std_year = str(props.get("gosi_year", "") or "")

        # jibun 예: "293대" → land_type = "대"
        jibun = str(props.get("jibun", "") or "")
        land_type_m = re.search(r"[가-힣]+$", jibun)
        land_type = land_type_m.group() if land_type_m else ""
        polygon_geojson = feature.get("geometry")

        # Step 2: NED Attr API → 연도별 공시지가 히스토리 (전체)
        price_history: list[dict] = []
        if pnu:
            try:
                attr_resp = await client.get(
                    VWORLD_NED_ATTR,
                    headers=headers,
                    params={
                        "pnu": pnu,
                        "format": "json",
                        "numOfRows": 100,
                        "key": settings.VWORLD_API_KEY,
                    },
                )
                if attr_resp.status_code == 200:
                    attr_data = attr_resp.json()
                    raw_items = attr_data.get("indvdLandPrices", {}).get("field", [])
                    if isinstance(raw_items, dict):
                        raw_items = [raw_items]
                    price_history = sorted(
                        [
                            {
                                "year": int(item.get("stdrYear", 0)),
                                "price_per_sqm": int(item.get("pblntfPclnd", 0) or 0),
                            }
                            for item in raw_items
                            if item.get("stdrYear") and item.get("pblntfPclnd")
                        ],
                        key=lambda x: x["year"],
                    )
            except Exception as e:
                logger.warning("공시지가 히스토리 조회 실패: %s", e)

        return {
            "pnu": pnu,
            "current_price_per_sqm": current_price,
            "std_year": std_year,
            "land_area_sqm": 0.0,
            "land_type": land_type,
            "polygon": polygon_geojson,
            "price_history": price_history,
        }
