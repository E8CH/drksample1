"""
Tests for POST /simulation/run endpoint.

Unit tests (TestHelpers): pure logic, no DB.
Integration tests (TestSimulationRoute): mock AsyncSession via dependency override.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import jwt
from httpx import AsyncClient, ASGITransport
from fastapi import status

from app.config import settings
from app.database import get_async_session
from app.main import app
from app.engines.rule_based import extract_gu, extract_si, _calc_verdict


def _make_token(username: str = "admin", expired: bool = False) -> str:
    delta = timedelta(seconds=-1) if expired else timedelta(hours=1)
    exp = datetime.now(timezone.utc) + delta
    return jwt.encode({"sub": username, "exp": exp}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _empty_db_session():
    """AsyncSession mock that returns empty results (triggers fallback path)."""
    mock_session = AsyncMock()
    empty_scalars = MagicMock()
    empty_scalars.all.return_value = []
    empty_result = MagicMock()
    empty_result.scalars.return_value = empty_scalars
    empty_result.all.return_value = []
    mock_session.execute.return_value = empty_result
    return mock_session


@pytest_asyncio.fixture
async def sim_client():
    """Test client with mocked DB session — no real DB required."""
    async def override():
        yield _empty_db_session()

    app.dependency_overrides[get_async_session] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as client:
        yield client
    app.dependency_overrides.pop(get_async_session, None)


# ── Pure unit tests (no DB) ──────────────────────────────────────────────────

class TestHelpers:
    def test_extract_gu_standard(self):
        assert extract_gu("서울 강남구 역삼동 123") == "강남구"

    def test_extract_gu_no_gu(self):
        assert extract_gu("서울시") == ""

    def test_extract_si_standard(self):
        assert extract_si("서울시 강남구 역삼동") == "서울시"

    def test_extract_si_no_si(self):
        assert extract_si("강남구") == ""

    def test_calc_verdict_추천(self):
        assert _calc_verdict(70.0) == "추천"
        assert _calc_verdict(100.0) == "추천"

    def test_calc_verdict_검토필요(self):
        assert _calc_verdict(40.0) == "검토필요"
        assert _calc_verdict(69.9) == "검토필요"

    def test_calc_verdict_비추천(self):
        assert _calc_verdict(0.0) == "비추천"
        assert _calc_verdict(39.9) == "비추천"


# ── Integration tests (mocked DB) ────────────────────────────────────────────

VALID_PAYLOAD = {
    "address": "서울 강남구 역삼동 123",
    "area_sqm": 200.0,
    "monthly_rent": 3000000.0,
    "ev_charging": False,
    "parking_count": 5,
}


class TestSimulationRoute:
    @pytest.mark.asyncio(loop_scope="function")
    async def test_unauthenticated_returns_401(self, sim_client):
        res = await sim_client.post("/simulation/run", json=VALID_PAYLOAD)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio(loop_scope="function")
    async def test_expired_token_returns_401(self, sim_client):
        token = _make_token(expired=True)
        res = await sim_client.post(
            "/simulation/run",
            json=VALID_PAYLOAD,
            cookies={"access_token": token},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio(loop_scope="function")
    async def test_valid_request_returns_200_with_fallback(self, sim_client):
        """Empty DB → fallback_used=True but schema must be valid."""
        token = _make_token()
        res = await sim_client.post(
            "/simulation/run",
            json=VALID_PAYLOAD,
            cookies={"access_token": token},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "estimated_monthly_revenue" in data
        assert "occupancy_rate" in data
        assert "net_profit" in data
        assert "percentile" in data
        assert data["verdict"] in ("추천", "검토필요", "비추천")
        assert isinstance(data["similar_branch_count"], int)
        assert data["fallback_used"] is True
        assert "comparison_data" in data
        assert isinstance(data["comparison_data"], list)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_ev_charging_increases_revenue(self, sim_client):
        """EV=True revenue must be 1.08× EV=False revenue (fallback _default_estimate path)."""
        token = _make_token()
        base_payload = {**VALID_PAYLOAD, "ev_charging": False}
        ev_payload = {**VALID_PAYLOAD, "ev_charging": True}
        res_base = await sim_client.post("/simulation/run", json=base_payload, cookies={"access_token": token})
        res_ev = await sim_client.post("/simulation/run", json=ev_payload, cookies={"access_token": token})
        assert res_base.status_code == status.HTTP_200_OK
        assert res_ev.status_code == status.HTTP_200_OK
        rev_base = res_base.json()["estimated_monthly_revenue"]
        rev_ev = res_ev.json()["estimated_monthly_revenue"]
        assert rev_ev == pytest.approx(rev_base * 1.08, rel=1e-3)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_invalid_payload_returns_422(self, sim_client):
        token = _make_token()
        bad = {"address": "", "area_sqm": -1, "monthly_rent": 0}
        res = await sim_client.post(
            "/simulation/run",
            json=bad,
            cookies={"access_token": token},
        )
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
