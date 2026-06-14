import httpx

from app.config import settings
from app.providers.base import MapProvider
from app.schemas.map import BranchPin, Coordinates


class KakaoMapProvider(MapProvider):
    BASE_URL = "https://dapi.kakao.com/v2/local"

    async def geocode(self, address: str) -> Coordinates:
        headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/search/address.json",
                params={"query": address},
                headers=headers,
            )
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            if not docs:
                raise ValueError(f"주소 '{address}'에 대한 지오코딩 결과 없음")
            return Coordinates(
                latitude=float(docs[0]["y"]),
                longitude=float(docs[0]["x"]),
            )

    async def get_nearby_branches(
        self, coords: Coordinates, radius_km: float
    ) -> list[BranchPin]:
        # Story 3.1에서 DB 조회 + 지도 핀 렌더링으로 구현
        return []
