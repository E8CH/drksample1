import logging

from app.config import settings
from app.providers.kakao import KakaoMapProvider
from app.providers.juso import JusoMapProvider
from app.providers.nominatim import NominatimMapProvider
from app.providers.vworld import VWorldMapProvider
from app.schemas.map import Coordinates

_juso = JusoMapProvider()
_kakao = KakaoMapProvider()
_vworld = VWorldMapProvider()
_nominatim = NominatimMapProvider()

logger = logging.getLogger(__name__)

_PLACEHOLDER_KAKAO_KEY = "test-kakao-key-placeholder"


async def geocode(address: str) -> Coordinates:
    # 1순위: Kakao Local API (글로벌 IP에서 작동, 한국 주소 정확도 최고)
    kakao_key = settings.KAKAO_REST_API_KEY or ""
    if kakao_key and kakao_key != _PLACEHOLDER_KAKAO_KEY:
        try:
            return await _kakao.geocode(address)
        except Exception as e:
            logger.warning("Kakao geocoding failed (%s), trying Juso", e)

    # 2순위: Juso 좌표 API (키가 coord API까지 승인된 경우)
    if settings.JUSO_API_KEY:
        try:
            return await _juso.geocode(address)
        except Exception as e:
            logger.warning("Juso geocoding failed (%s), trying VWORLD", e)

    # 3순위: VWORLD 주소 API (한국 내부 IP에서만 동작할 수 있음)
    if settings.VWORLD_API_KEY:
        try:
            return await _vworld.geocode(address)
        except Exception as e:
            logger.warning("VWORLD geocoding failed (%s), falling back to Nominatim", e)

    # 4순위: Nominatim (최후 수단, 정확도 낮음)
    return await _nominatim.geocode(address)
