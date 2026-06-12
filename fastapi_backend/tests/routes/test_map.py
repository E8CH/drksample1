"""
Tests for GET /branches/nearby endpoint.

Integration tests using mock for KakaoMapProvider.geocode and empty DB session.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
from httpx import AsyncClient, ASGITransport

from app.config import settings
from app.database import get_async_session
from app.main import app
from app.routes.map import _haversine_km


def _make_token(username: str = "admin", expired: bool = False) -> str:
    delta = timedelta(seconds=-1) if expired else timedelta(hours=1)
    exp = datetime.now(timezone.utc) + delta
    return jwt.encode({"sub": username, "exp": exp}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _empty_db_session():
    mock_session = AsyncMock()
    empty_scalars = MagicMock()
    empty_scalars.all.return_value = []
    empty_result = MagicMock()
    empty_result.scalars.return_value = empty_scalars
    mock_session.execute.return_value = empty_result
    return mock_session


@pytest_asyncio.fixture
async def map_client():
    app.dependency_overrides[get_async_session] = lambda: _empty_db_session()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ── Unit tests ─────────────────────────────────────────────────────────────

class TestHaversine:
    def test_same_point_is_zero(self):
        assert _haversine_km(37.5, 127.0, 37.5, 127.0) == pytest.approx(0.0, abs=0.001)

    def test_one_km_north(self):
        # ~1km north: 0.009° latitude ≈ 1km
        dist = _haversine_km(37.5, 127.0, 37.509, 127.0)
        assert 0.9 < dist < 1.2

    def test_symmetric(self):
        d1 = _haversine_km(37.5, 127.0, 37.6, 127.1)
        d2 = _haversine_km(37.6, 127.1, 37.5, 127.0)
        assert d1 == pytest.approx(d2, abs=0.001)


# ── Integration tests ───────────────────────────────────────────────────────

class TestNearbyBranchesRoute:
    async def test_unauthenticated_returns_401(self, map_client: AsyncClient):
        resp = await map_client.get("/branches/nearby", params={"address": "서울 강남구"})
        assert resp.status_code == 401

    async def test_expired_token_returns_401(self, map_client: AsyncClient):
        token = _make_token(expired=True)
        resp = await map_client.get(
            "/branches/nearby",
            params={"address": "서울 강남구"},
            cookies={"access_token": token},
        )
        assert resp.status_code == 401

    async def test_geocode_success_returns_200_with_empty_pins(self, map_client: AsyncClient):
        token = _make_token()
        from app.schemas.map import Coordinates
        mock_coords = Coordinates(latitude=37.498, longitude=127.028)
        with patch("app.services.map_service.geocode", return_value=mock_coords):
            resp = await map_client.get(
                "/branches/nearby",
                params={"address": "서울 강남구 역삼동"},
                cookies={"access_token": token},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["target"]["latitude"] == pytest.approx(37.498)
        assert data["target"]["longitude"] == pytest.approx(127.028)
        assert data["pins"] == []

    async def test_geocode_failure_returns_422(self, map_client: AsyncClient):
        token = _make_token()
        with patch("app.services.map_service.geocode", side_effect=ValueError("주소 없음")):
            resp = await map_client.get(
                "/branches/nearby",
                params={"address": "존재하지않는주소xyz"},
                cookies={"access_token": token},
            )
        assert resp.status_code == 422

    async def test_missing_address_returns_422(self, map_client: AsyncClient):
        token = _make_token()
        resp = await map_client.get(
            "/branches/nearby",
            cookies={"access_token": token},
        )
        assert resp.status_code == 422
