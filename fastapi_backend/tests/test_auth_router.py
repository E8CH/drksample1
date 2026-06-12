import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import settings


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as c:
        yield c


@pytest.mark.asyncio(loop_scope="function")
async def test_login_success(client):
    response = await client.post(
        "/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ok"
    assert "access_token" in data and isinstance(data["access_token"], str)
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "HttpOnly" in set_cookie


@pytest.mark.asyncio(loop_scope="function")
async def test_login_wrong_password(client):
    response = await client.post(
        "/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "로그인 정보가 올바르지 않습니다"


@pytest.mark.asyncio(loop_scope="function")
async def test_login_wrong_username(client):
    response = await client.post(
        "/auth/login",
        json={"username": "notadmin", "password": settings.ADMIN_PASSWORD},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "로그인 정보가 올바르지 않습니다"


@pytest.mark.asyncio(loop_scope="function")
async def test_logout_deletes_cookie(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert 'max-age=0' in set_cookie.lower() or 'expires=' in set_cookie.lower()
