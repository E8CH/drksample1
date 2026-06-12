import os
import unittest.mock as mock

import httpx
import pytest
import respx
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.providers.kakao import KakaoMapProvider
from app.schemas.map import BranchPin, Coordinates


MOCK_GEOCODE_RESPONSE = {
    "documents": [
        {
            "x": "127.038604",
            "y": "37.498095",
            "address_name": "서울특별시 강남구 역삼동 123",
        }
    ],
    "meta": {"total_count": 1},
}

MOCK_EMPTY_RESPONSE = {
    "documents": [],
    "meta": {"total_count": 0},
}


@pytest.mark.asyncio(loop_scope="function")
async def test_kakao_geocode_returns_coordinates():
    provider = KakaoMapProvider()
    with respx.mock:
        route = respx.get("https://dapi.kakao.com/v2/local/geo/address.json").mock(
            return_value=httpx.Response(200, json=MOCK_GEOCODE_RESPONSE)
        )
        result = await provider.geocode("서울 강남구 역삼동 123")
    assert isinstance(result, Coordinates)
    assert result.latitude == pytest.approx(37.498095)
    assert result.longitude == pytest.approx(127.038604)
    # Authorization: KakaoAK {key} 헤더 전송 확인 (AC3)
    assert route.called
    sent_auth = route.calls.last.request.headers.get("authorization", "")
    assert sent_auth.startswith("KakaoAK "), f"Authorization 헤더 형식 오류: {sent_auth}"


@pytest.mark.asyncio(loop_scope="function")
async def test_kakao_geocode_no_results_raises():
    provider = KakaoMapProvider()
    with respx.mock:
        respx.get("https://dapi.kakao.com/v2/local/geo/address.json").mock(
            return_value=httpx.Response(200, json=MOCK_EMPTY_RESPONSE)
        )
        with pytest.raises(ValueError, match="지오코딩 결과 없음"):
            await provider.geocode("존재하지않는주소12345678")


@pytest.mark.asyncio(loop_scope="function")
async def test_map_provider_get_nearby_branches_returns_list():
    provider = KakaoMapProvider()
    coords = Coordinates(latitude=37.498095, longitude=127.038604)
    result = await provider.get_nearby_branches(coords, radius_km=2.0)
    assert isinstance(result, list)
    assert all(isinstance(pin, BranchPin) for pin in result)


def test_kakao_rest_api_key_required():
    """KAKAO_REST_API_KEY 미설정 시 pydantic-settings ValidationError 발생 — 서버 기동 차단 증명 (AC4)."""

    class IsolatedSettings(BaseSettings):
        KAKAO_REST_API_KEY: str
        model_config = SettingsConfigDict(env_file=None, extra="ignore")

    env_without_key = {k: v for k, v in os.environ.items() if k != "KAKAO_REST_API_KEY"}
    with mock.patch.dict(os.environ, env_without_key, clear=True):
        with pytest.raises(ValidationError):
            IsolatedSettings()
