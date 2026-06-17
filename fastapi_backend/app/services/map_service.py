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
    # 1순위: Juso 도로명 주소 조회 → Nominatim
    # 지번 주소를 도로명으로 변환하면 Nominatim 정확도가 크게 향상됨 (~12m 오차)
    if settings.JUSO_API_KEY:
        try:
            road_addr = await _juso.get_road_address(address)
            if road_addr:
                logger.info("Juso road address resolved: %s → %s", address, road_addr)
                return await _nominatim.geocode(road_addr)
        except Exception as e:
            logger.warning("Juso+Nominatim failed (%s), trying VWORLD", e)

    # 2순위: VWORLD 주소 API (한국 내부 IP에서만 동작)
    if settings.VWORLD_API_KEY:
        try:
            return await _vworld.geocode(address)
        except Exception as e:
            logger.warning("VWORLD geocoding failed (%s), falling back to Nominatim", e)

    # 3순위: Nominatim with original address (최후 수단)
    return await _nominatim.geocode(address)
