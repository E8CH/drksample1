import httpx

from app.providers.base import MapProvider
from app.schemas.map import BranchPin, Coordinates


class NominatimMapProvider(MapProvider):
    BASE_URL = "https://nominatim.openstreetmap.org"

    async def geocode(self, address: str) -> Coordinates:
        async with httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "drksample1/1.0", "Accept-Language": "ko"},
        ) as client:
            # 1차 시도: 한국 한정 검색
            for query in self._address_candidates(address):
                resp = await client.get(
                    f"{self.BASE_URL}/search",
                    params={"q": query, "format": "json", "limit": 1, "countrycodes": "kr"},
                )
                resp.raise_for_status()
                results = resp.json()
                if results:
                    return Coordinates(
                        latitude=float(results[0]["lat"]),
                        longitude=float(results[0]["lon"]),
                    )
        raise ValueError(f"주소 '{address}'에 대한 지오코딩 결과 없음")

    @staticmethod
    def _address_candidates(address: str) -> list[str]:
        """원본 주소 → 점진적으로 단순화한 후보 목록 반환."""
        import re
        candidates = [address]
        # 끝에 붙은 숫자/번지 제거 (역삼동123 → 역삼동)
        simplified = re.sub(r"\s*\d+[-\d]*\s*$", "", address).strip()
        if simplified and simplified != address:
            candidates.append(simplified)
        # 시/구/동 단위만 남기기 (앞 2개 토큰)
        tokens = address.split()
        if len(tokens) > 2:
            candidates.append(" ".join(tokens[:2]))
        return candidates

    async def get_nearby_branches(
        self, coords: Coordinates, radius_km: float
    ) -> list[BranchPin]:
        return []
