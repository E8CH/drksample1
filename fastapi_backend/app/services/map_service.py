import logging

from app.providers.kakao import KakaoMapProvider
from app.providers.nominatim import NominatimMapProvider
from app.schemas.map import BranchPin, Coordinates

_kakao = KakaoMapProvider()
_nominatim = NominatimMapProvider()

logger = logging.getLogger(__name__)


async def geocode(address: str) -> Coordinates:
    try:
        return await _kakao.geocode(address)
    except Exception as e:
        logger.warning("Kakao geocoding failed (%s), falling back to Nominatim", e)
        return await _nominatim.geocode(address)


async def get_nearby_branches(
    coords: Coordinates, radius_km: float = 2.0
) -> list[BranchPin]:
    return await _provider.get_nearby_branches(coords, radius_km)
