import httpx

from app.providers.base import MapProvider
from app.schemas.map import BranchPin, Coordinates


class NominatimMapProvider(MapProvider):
    BASE_URL = "https://nominatim.openstreetmap.org"

    async def geocode(self, address: str) -> Coordinates:
        async with httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "drksample1/1.0"},
        ) as client:
            resp = await client.get(
                f"{self.BASE_URL}/search",
                params={"q": address, "format": "json", "limit": 1},
            )
            resp.raise_for_status()
            results = resp.json()
            if not results:
                raise ValueError(f"주소 '{address}'에 대한 지오코딩 결과 없음")
            return Coordinates(
                latitude=float(results[0]["lat"]),
                longitude=float(results[0]["lon"]),
            )

    async def get_nearby_branches(
        self, coords: Coordinates, radius_km: float
    ) -> list[BranchPin]:
        return []
