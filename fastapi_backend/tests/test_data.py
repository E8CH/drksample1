from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import status

from app.config import settings
from app.services import data_generator as dg_module
from app.routes import data as routes_data_module


def _make_admin_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=3600)
    return jwt.encode(
        {"sub": settings.ADMIN_USERNAME, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


@pytest.mark.asyncio(loop_scope="function")
async def test_generate_unauthenticated(test_client):
    """POST /data/generate without token → 401."""
    response = await test_client.post("/data/generate")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio(loop_scope="function")
async def test_generate_authenticated(test_client):
    """POST /data/generate with valid admin token → 202."""
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.post("/data/generate")
    assert response.status_code == status.HTTP_202_ACCEPTED
    body = response.json()
    assert body["status"] == "generating"
    # reset module state after test
    dg_module._STATUS["value"] = "idle"


@pytest.mark.asyncio(loop_scope="function")
async def test_generate_conflict_when_running(test_client):
    """POST /data/generate while running → 409."""
    dg_module._STATUS["value"] = "running"
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.post("/data/generate")
    assert response.status_code == status.HTTP_409_CONFLICT
    # reset
    dg_module._STATUS["value"] = "idle"


@pytest.mark.asyncio(loop_scope="function")
async def test_status_unauthenticated(test_client):
    """GET /data/status without token → 401."""
    response = await test_client.get("/data/status")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio(loop_scope="function")
async def test_status_authenticated_idle(test_client):
    """GET /data/status with valid token → 200 with idle status."""
    dg_module._STATUS["value"] = "idle"
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/data/status")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "idle"


@pytest.mark.asyncio(loop_scope="function")
async def test_status_authenticated_running(test_client):
    """GET /data/status returns running when set."""
    dg_module._STATUS["value"] = "running"
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/data/status")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "running"
    # reset
    dg_module._STATUS["value"] = "idle"


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_all_unauthenticated(test_client):
    """DELETE /data/all without token → 401."""
    response = await test_client.delete("/data/all")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_all_authenticated(test_client, monkeypatch):
    """DELETE /data/all with valid admin token → 200."""
    async def mock_delete():
        pass
    monkeypatch.setattr(routes_data_module, "delete_all_data", mock_delete)
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.delete("/data/all")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["deleted"] is True


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_all_idempotent(test_client, monkeypatch):
    """DELETE /data/all called twice → both 200 (멱등성)."""
    async def mock_delete():
        pass
    monkeypatch.setattr(routes_data_module, "delete_all_data", mock_delete)
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    r1 = await test_client.delete("/data/all")
    r2 = await test_client.delete("/data/all")
    assert r1.status_code == status.HTTP_200_OK
    assert r2.status_code == status.HTTP_200_OK
    assert r2.json()["deleted"] is True


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_all_blocked_while_generating(test_client):
    """DELETE /data/all while generation running → 409."""
    dg_module._STATUS["value"] = "running"
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.delete("/data/all")
    assert response.status_code == status.HTTP_409_CONFLICT
    dg_module._STATUS["value"] = "idle"
