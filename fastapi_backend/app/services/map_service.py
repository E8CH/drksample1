import logging

from app.config import settings
from app.providers.juso import JusoMapProvider
from app.providers.nominatim import NominatimMapProvider
from app.providers.vworld import VWorldMapProvider
from app.schemas.map import Coordinates

_juso = JusoMapProvider()
_vworld = VWorldMapProvider()
_nominatim = NominatimMapProvider()

logger = logging.getLogger(__name__)


async def geocode(address: str) -> Coordinates:
    # 1순위: Juso 좌표 API (키가 coord API까지 승인된 경우)
    if settings.JUSO_API_KEY:
        try:
            return await _juso.geocode(address)
        except Exception as e:
            logger.warning("Juso geocoding failed (%s), trying VWORLD", e)

    # 2순위: VWORLD 주소 API (한국 주소 정확도 높음, 별도 키 불필요)
    if settings.VWORLD_API_KEY:
        try:
            return await _vworld.geocode(address)
        except Exception as e:
            logger.warning("VWORLD geocoding failed (%s), falling back to Nominatim", e)

    # 3순위: Nominatim (최후 수단, 정확도 낮음)
    return await _nominatim.geocode(address)
