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
_VWORLD_HOST = "https://api.vworld.kr"
VWORLD_2D_LAYER = "LP_PA_CBND_BUBUN"
VWORLD_REFERER = "https://frontend-production-7e58.up.railway.app/dashboard/simulation"


def _vworld_url(path: str) -> str:
    base = (settings.VWORLD_PROXY_URL or _VWORLD_HOST).rstrip("/")
    return base + path
_LAND_BBOX_DELTA = 0.0003  # ~30m
OVERPASS_URL = "https://lz4.overpass-api.de/api/interpreter"
_OVERPASS_BBOX_DELTA = 0.0005  # ~50m

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
            # Juso API가 Railway Singapore IP를 차단하거나 연결 불가 시 graceful 응답
            logger.warning("Juso API error (likely IP block): %s", e)
            return {"found": False, "road_address": address, "jibun_address": ""}

        try:
            juso_data = juso_resp.json()
        except Exception as e:
            logger.warning("Juso API JSON parse error: %s", e)
            return {"found": False, "road_address": address, "jibun_address": ""}

        error_code = juso_data.get("results", {}).get("common", {}).get("errorCode", "0")
        if error_code != "0":
            logger.warning("Juso API error code: %s", error_code)
            return {"found": False, "road_address": address, "jibun_address": ""}

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

        # Step 3: 호수별 전유/공용 면적 — API가 numOfRows를 무시하고 1개씩 반환하므로 페이지네이션
        expo_params = {**bld_params, "numOfRows": 100}
        expo_items: list = []
        try:
            for page_no in range(1, 201):  # 최대 200페이지 (200×100=20,000호)
                expo_params["pageNo"] = page_no
                expo_resp = await client.get(
                    f"{BLDRGST_BASE}/getBrExposPubuseAreaInfo", params=expo_params
                )
                expo_resp.raise_for_status()
                expo_raw = expo_resp.json()
                body = expo_raw.get("response", {}).get("body", {})
                total_count = int(body.get("totalCount") or 0)
                page_items = _items_as_list(body.get("items", {}).get("item"))
                expo_items.extend(page_items)
                if not page_items or len(expo_items) >= total_count:
                    break
        except httpx.HTTPError as e:
            logger.warning("BldRgst expo API error: %s", e)
            expo_items = []

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


import math


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _elements_to_polygon(elements: list, lat: float, lon: float, max_dist_m: float = 80) -> dict | None:
    """elements 중 타겟에서 max_dist_m 이내 최근접 건물 → GeoJSON Polygon. 없으면 None."""
    def _center_dist(el: dict) -> float:
        b = el.get("bounds", {})
        if not b:
            return float("inf")
        return _haversine_m(lat, lon, (b["minlat"] + b["maxlat"]) / 2, (b["minlon"] + b["maxlon"]) / 2)

    candidates = [el for el in elements if _center_dist(el) <= max_dist_m]
    if not candidates:
        return None

    way = min(candidates, key=_center_dist)
    geometry = way.get("geometry", [])
    if len(geometry) < 3:
        return None

    coords = [[g["lon"], g["lat"]] for g in geometry]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return {"type": "Polygon", "coordinates": [coords]}


async def _fetch_osm_building_polygon(
    lat: float, lon: float, client: httpx.AsyncClient, name: str = ""
) -> dict | None:
    """Overpass API로 건물 footprint 폴리곤 조회 (IP 제한 없음).

    1) 건물명이 있으면 name 매칭 우선 탐색 (500m 반경)
    2) 위치 기반 around:80 탐색 (80m 초과 건물은 폴리곤 반환 거부)
    """
    headers = {"User-Agent": "drksample1/1.0"}

    # 1) 이름 매칭 시도
    if name:
        escaped = name.replace('"', '\\"')
        q_name = (
            f'[out:json][timeout:12];'
            f'way["building"]["name"~"{escaped}"](around:500,{lat},{lon});'
            f'out geom;'
        )
        try:
            r = await client.get(OVERPASS_URL, params={"data": q_name}, headers=headers, timeout=14.0)
            r.raise_for_status()
            els = r.json().get("elements", [])
            poly = _elements_to_polygon(els, lat, lon, max_dist_m=500)
            if poly:
                logger.info("Overpass 이름 매칭 성공: %s", name)
                return poly
        except Exception as e:
            logger.warning("Overpass 이름 탐색 실패: %s", e)

    # 2) 위치 기반 탐색 (80m 이내만 허용)
    q_loc = (
        f'[out:json][timeout:12];'
        f'way["building"](around:80,{lat},{lon});'
        f'out geom;'
    )
    try:
        r = await client.get(OVERPASS_URL, params={"data": q_loc}, headers=headers, timeout=14.0)
        r.raise_for_status()
        els = r.json().get("elements", [])
        poly = _elements_to_polygon(els, lat, lon, max_dist_m=80)
        if poly:
            return poly
        logger.info("Overpass: 80m 이내 건물 없음 (lat=%s, lon=%s)", lat, lon)
    except Exception as e:
        logger.warning("Overpass 위치 탐색 실패: %s", e)

    return None


@router.get("/land")
async def get_land_info(
    lat: float = Query(...),
    lon: float = Query(...),
    name: str = Query(default=""),
    _: str = Depends(require_admin),
) -> dict:
    import re

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Step 1: OSM Overpass → 건물 footprint 폴리곤 (IP 제한 없음)
        polygon_geojson = await _fetch_osm_building_polygon(lat, lon, client, name=name)

        # Step 2: VWORLD → 공시지가 (한국 IP에서만 작동, 실패 시 graceful)
        pnu = ""
        current_price = 0
        std_year = ""
        land_type = ""
        price_history: list[dict] = []
        vworld_polygon: dict | None = None

        if settings.VWORLD_API_KEY:
            d = _LAND_BBOX_DELTA
            geom_filter = f"BOX({lon - d},{lat - d},{lon + d},{lat + d})"
            vworld_headers = {"Referer": VWORLD_REFERER}
            try:
                data_resp = await client.get(
                    _vworld_url("/req/data"),
                    headers=vworld_headers,
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
                resp_json = data_resp.json()
                if resp_json.get("response", {}).get("status") == "OK":
                    features = (
                        resp_json.get("response", {})
                        .get("result", {})
                        .get("featureCollection", {})
                        .get("features", [])
                    )
                    if features:
                        props = features[0].get("properties", {})
                        pnu = str(props.get("pnu", "") or "")
                        current_price = int(props.get("jiga", 0) or 0)
                        std_year = str(props.get("gosi_year", "") or "")
                        jibun = str(props.get("jibun", "") or "")
                        m = re.search(r"[가-힣]+$", jibun)
                        land_type = m.group() if m else ""
                        vworld_polygon = features[0].get("geometry") or None
            except Exception as e:
                logger.warning("VWORLD 2D Data 실패 (IP 차단 가능성): %s", e)

            # Step 2b: NED Attr → 연도별 공시지가 히스토리
            if pnu:
                try:
                    attr_resp = await client.get(
                        _vworld_url("/ned/data/getIndvdLandPriceAttr"),
                        headers=vworld_headers,
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

    if polygon_geojson is None and vworld_polygon:
        polygon_geojson = vworld_polygon
        logger.info("OSM 폴리곤 없음 — VWORLD 필지 폴리곤 fallback 사용")

    if polygon_geojson is None and not pnu:
        raise HTTPException(status_code=404, detail="건물 및 필지 정보를 찾을 수 없습니다")

    return {
        "pnu": pnu,
        "current_price_per_sqm": current_price,
        "std_year": std_year,
        "land_area_sqm": 0.0,
        "land_type": land_type,
        "polygon": polygon_geojson,
        "price_history": price_history,
    }
