import logging

from app.config import settings
from app.providers.juso import JusoMapProvider
from app.providers.nominatim import NominatimMapProvider
from app.schemas.map import BranchPin, Coordinates

_juso = JusoMapProvider()
_nominatim = NominatimMapProvider()

logger = logging.getLogger(__name__)


async def geocode(address: str) -> Coordinates:
    # Juso 공공 API 우선 (한국 주소 정확도 높음)
    if settings.JUSO_API_KEY:
        try:
            return await _juso.geocode(address)
        except Exception as e:
            logger.warning("Juso geocoding failed (%s), falling back to Nominatim", e)
    return await _nominatim.geocode(address)


async def get_nearby_branches(
    coords: Coordinates, radius_km: float = 2.0
) -> list[BranchPin]:
    return await _provider.get_nearby_branches(coords, radius_km)
