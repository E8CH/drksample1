from app.providers.kakao import KakaoMapProvider
from app.schemas.map import BranchPin, Coordinates

_provider = KakaoMapProvider()


async def geocode(address: str) -> Coordinates:
    return await _provider.geocode(address)


async def get_nearby_branches(
    coords: Coordinates, radius_km: float = 2.0
) -> list[BranchPin]:
    return await _provider.get_nearby_branches(coords, radius_km)
