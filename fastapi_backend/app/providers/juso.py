import logging

import httpx

from app.config import settings
from app.providers.base import MapProvider
from app.schemas.map import BranchPin, Coordinates

logger = logging.getLogger(__name__)

JUSO_SEARCH_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
JUSO_COORD_URL = "https://business.juso.go.kr/addrlink/addrCoordApi.do"


class JusoMapProvider(MapProvider):
    async def get_road_address(self, address: str) -> str | None:
        """Juso 검색으로 도로명 주소 반환 — coord API 권한 없어도 작동."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                JUSO_SEARCH_URL,
                params={
                    "confmKey": settings.JUSO_API_KEY,
                    "currentPage": 1,
                    "countPerPage": 1,
                    "keyword": address,
                    "resultType": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            error_code = data.get("results", {}).get("common", {}).get("errorCode", "0")
            if error_code != "0":
                return None
            juso_list = data.get("results", {}).get("juso") or []
            if not juso_list:
                return None
            return juso_list[0].get("roadAddrPart1") or None

    async def geocode(self, address: str) -> Coordinates:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: 주소 검색 → rnMgtSn, udrtYn, buldMnnm, buldSlno 획득
            search_resp = await client.get(
                JUSO_SEARCH_URL,
                params={
                    "confmKey": settings.JUSO_API_KEY,
                    "currentPage": 1,
                    "countPerPage": 1,
                    "keyword": address,
                    "resultType": "json",
                },
            )
            search_resp.raise_for_status()
            search_data = search_resp.json()

            error_code = search_data.get("results", {}).get("common", {}).get("errorCode", "0")
            if error_code != "0":
                raise ValueError(f"Juso API 오류: {error_code}")

            juso_list = search_data.get("results", {}).get("juso") or []
            if not juso_list:
                raise ValueError(f"주소 '{address}'를 찾을 수 없습니다")

            j = juso_list[0]

            # Step 2: 좌표 조회
            coord_resp = await client.get(
                JUSO_COORD_URL,
                params={
                    "confmKey": settings.JUSO_API_KEY,
                    "admCd": j.get("admCd", ""),
                    "rnMgtSn": j.get("rnMgtSn", ""),
                    "udrtYn": j.get("udrtYn", "0"),
                    "buldMnnm": j.get("buldMnnm", 0),
                    "buldSlno": j.get("buldSlno", 0),
                    "resultType": "json",
                },
            )
            coord_resp.raise_for_status()
            coord_data = coord_resp.json()

            coord_list = coord_data.get("results", {}).get("juso") or []
            if not coord_list:
                raise ValueError(f"주소 '{address}'의 좌표를 찾을 수 없습니다")

            c = coord_list[0]
            lat = float(c.get("lat") or 0)
            lon = float(c.get("lon") or 0)
            if not lat or not lon:
                raise ValueError(f"좌표값 없음: {c}")

            logger.info("Juso geocode OK: %s → lat=%s lon=%s", address, lat, lon)
            return Coordinates(latitude=lat, longitude=lon)

    async def get_nearby_branches(
        self, coords: Coordinates, radius_km: float
    ) -> list[BranchPin]:
        return []
