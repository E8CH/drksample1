import asyncio
import logging
import math
import re
import time
from collections import defaultdict
from datetime import date

import httpx
import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query

from app.config import settings

router = APIRouter(prefix="/building", tags=["building"])
logger = logging.getLogger(__name__)

JUSO_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
JUSO_COORD_URL = "https://business.juso.go.kr/addrlink/addrCoordApi.do"
BLDRGST_BASE = "http://apis.data.go.kr/1613000/BldRgstHubService"
RTM_BASE = "http://apis.data.go.kr/1613000"
_VWORLD_HOST = "https://api.vworld.kr"
VWORLD_2D_LAYER = "LP_PA_CBND_BUBUN"
VWORLD_REFERER = "https://frontend-production-7e58.up.railway.app/dashboard/simulation"
OVERPASS_URL = "https://lz4.overpass-api.de/api/interpreter"
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
        oldest = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest]
    _cache[key] = (time.time(), value)


# ── Rate limiter: 건축물대장 외부 API 분당 최대 5회 ────────────────────────
_EXT_RATE_LIMIT = 5
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


def _vworld_url(path: str) -> str:
    base = (settings.VWORLD_PROXY_URL or _VWORLD_HOST).rstrip("/")
    return base + path


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


# ── /building/info ─────────────────────────────────────────────────────────

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

    _check_rate_limit()

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Step 1: Juso API → admCd + 지번
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

        # Step 1-b: Juso 좌표 API — 위경도 획득
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

        title = next(
            (t for t in title_items if "표제부" in (t.get("regstrKindCdNm") or "")),
            title_items[0],
        )

        # Step 3: 호수별 전유/공용 면적 — 페이지네이션
        expo_params = {**bld_params, "numOfRows": 100}
        expo_items: list = []
        try:
            for page_no in range(1, 201):
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
            "sigungu_cd": sigungu_cd,
            "bun": bun,
        }
        _cache_set(cache_key, result)
        return result


# ── Overpass / VWORLD 헬퍼 ─────────────────────────────────────────────────

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _elements_to_polygon(elements: list, lat: float, lon: float, max_dist_m: float = 80) -> dict | None:
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
    """Overpass 건물 footprint 조회. name/location 쿼리를 병렬로 실행."""
    headers = {"User-Agent": "drksample1/1.0"}

    async def _query(q: str, dist: float) -> dict | None:
        try:
            r = await client.get(OVERPASS_URL, params={"data": q}, headers=headers, timeout=14.0)
            r.raise_for_status()
            return _elements_to_polygon(r.json().get("elements", []), lat, lon, max_dist_m=dist)
        except Exception as e:
            logger.warning("Overpass 탐색 실패: %s", e)
            return None

    q_loc = f'[out:json][timeout:12];way["building"](around:80,{lat},{lon});out geom;'

    if name:
        escaped = name.replace('"', '\\"')
        q_name = f'[out:json][timeout:12];way["building"]["name"~"{escaped}"](around:500,{lat},{lon});out geom;'
        name_poly, loc_poly = await asyncio.gather(
            _query(q_name, 500),
            _query(q_loc, 80),
        )
        if name_poly:
            logger.info("Overpass 이름 매칭 성공: %s", name)
            return name_poly
        if loc_poly:
            return loc_poly
        logger.info("Overpass: 건물 없음 (lat=%s, lon=%s)", lat, lon)
        return None

    return await _query(q_loc, 80)


async def _fetch_vworld_land(
    lat: float, lon: float, client: httpx.AsyncClient
) -> tuple:
    """VWORLD 필지 조회 → (pnu, current_price, std_year, land_type, vworld_polygon, price_history)"""
    pnu = ""
    current_price = 0
    std_year = ""
    land_type = ""
    vworld_polygon = None
    price_history: list[dict] = []

    if not settings.VWORLD_API_KEY:
        return pnu, current_price, std_year, land_type, vworld_polygon, price_history

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
        logger.warning("VWORLD 2D Data 실패: %s", e)

    # NED 연도별 공시지가 (PNU 필요 → 순차)
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

    return pnu, current_price, std_year, land_type, vworld_polygon, price_history


# ── /building/land ─────────────────────────────────────────────────────────

@router.get("/land")
async def get_land_info(
    lat: float = Query(...),
    lon: float = Query(...),
    name: str = Query(default=""),
    _: str = Depends(require_admin),
) -> dict:
    land_cache_key = f"land:{round(lat, 5)}:{round(lon, 5)}"
    cached_land = _cache_get(land_cache_key)
    if cached_land:
        # name이 있고 캐시에 polygon이 없으면 Overpass 재시도 가치 있음
        if not (name and cached_land.get("polygon") is None):
            logger.info("Land cache hit: %s", land_cache_key)
            return cached_land

    async with httpx.AsyncClient(timeout=20.0) as client:
        # Overpass + VWORLD 병렬 실행
        polygon_geojson, (pnu, current_price, std_year, land_type, vworld_polygon, price_history) = (
            await asyncio.gather(
                _fetch_osm_building_polygon(lat, lon, client, name=name),
                _fetch_vworld_land(lat, lon, client),
            )
        )

    if polygon_geojson is None and vworld_polygon:
        polygon_geojson = vworld_polygon
        logger.info("OSM 폴리곤 없음 — VWORLD 필지 폴리곤 fallback 사용")

    if polygon_geojson is None and not pnu:
        raise HTTPException(status_code=404, detail="건물 및 필지 정보를 찾을 수 없습니다")

    result = {
        "pnu": pnu,
        "current_price_per_sqm": current_price,
        "std_year": std_year,
        "land_area_sqm": 0.0,
        "land_type": land_type,
        "polygon": polygon_geojson,
        "price_history": price_history,
    }
    _cache_set(land_cache_key, result)
    return result


# ── /building/rent ─────────────────────────────────────────────────────────

@router.get("/rent")
async def get_building_rent(
    sigungu_cd: str = Query(..., min_length=5, max_length=5),
    bun: str = Query(..., min_length=4, max_length=4),
    name: str = Query(default=""),
    _: str = Depends(require_admin),
) -> dict:
    if not settings.RTM_API_KEY:
        raise HTTPException(status_code=503, detail="실거래가 API 키 미설정 (RTM_API_KEY)")

    bun_int = str(int(bun))  # "0290" → "290"

    # 최근 24개월
    today = date.today()
    months: list[str] = []
    y, mo = today.year, today.month
    for _ in range(24):
        months.append(f"{y}{mo:02d}")
        mo -= 1
        if mo == 0:
            mo, y = 12, y - 1

    endpoint = f"{RTM_BASE}/RTMSDataSvcNrtTrade/getRTMSDataSvcNrtTrade"

    async def fetch_month(ym: str, client: httpx.AsyncClient) -> list[dict]:
        try:
            r = await client.get(
                endpoint,
                params={
                    "serviceKey": settings.BUILDING_API_KEY,
                    "LAWD_CD": sigungu_cd,
                    "DEAL_YMD": ym,
                    "numOfRows": 100,
                    "_type": "json",
                },
                timeout=10.0,
            )
            if r.status_code != 200:
                return []
            body = r.json().get("response", {}).get("body", {})
            items = _items_as_list(body.get("items", {}).get("item"))
            matched = []
            for item in items:
                jibun = str(item.get("지번") or "")
                bld_name = str(item.get("건물명") or "")
                if bun_int in jibun.split() or bun_int == jibun or (name and name in bld_name):
                    matched.append({**item, "_ym": ym})
            return matched
        except Exception as e:
            logger.warning("RTM %s 조회 실패: %s", ym, e)
            return []

    async with httpx.AsyncClient(timeout=15.0) as client:
        month_results = await asyncio.gather(*[fetch_month(ym, client) for ym in months])

    all_items = [item for items in month_results for item in items]

    transactions = []
    for item in all_items:
        ym = item.get("_ym", "")
        year = str(item.get("년") or ym[:4])
        month_str = str(item.get("월") or ym[4:6]).zfill(2)
        amount_raw = str(item.get("거래금액") or "").replace(",", "").strip()
        try:
            amount_wan = int(amount_raw)
        except (ValueError, TypeError):
            amount_wan = 0

        transactions.append({
            "date": f"{year}-{month_str}",
            "amount_wan": amount_wan,
            "floor": str(item.get("층") or ""),
            "area_sqm": float(item.get("전용면적") or 0),
            "building_name": str(item.get("건물명") or ""),
            "land_use": str(item.get("용도지역") or ""),
        })

    transactions.sort(key=lambda x: x["date"], reverse=True)
    return {"transactions": transactions}
