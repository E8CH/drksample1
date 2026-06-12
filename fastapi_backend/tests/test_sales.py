from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import status

from app.config import settings


def _make_admin_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=3600)
    return jwt.encode(
        {"sub": settings.ADMIN_USERNAME, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_unauthenticated(test_client):
    """GET /sales without token → 401."""
    response = await test_client.get("/sales")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_authenticated_empty(test_client):
    """GET /sales with valid admin token → 200, empty data list."""
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/sales")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "data" in body
    assert "total" in body
    assert "page" in body
    assert "limit" in body
    assert isinstance(body["data"], list)
    assert body["page"] == 1
    assert body["limit"] == 50


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_invalid_sort_by(test_client):
    """GET /sales with invalid sort_by → 422 Unprocessable Entity."""
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/sales?sort_by=invalid_column")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_default_sort(test_client):
    """GET /sales defaults: sort_by=sale_date, order=desc, page=1, limit=50."""
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/sales")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["page"] == 1
    assert body["limit"] == 50


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_year_filter(test_client):
    """GET /sales?year=2025 — valid param accepted (200 even if empty)."""
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/sales?year=2025")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_branch_name_filter(test_client):
    """GET /sales?branch_name=강남 — ILIKE filter accepted (200 even if empty)."""
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/sales?branch_name=강남")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_ascending_sort(test_client):
    """GET /sales?sort_by=monthly_revenue&order=asc — valid combination accepted."""
    token = _make_admin_token()
    test_client.cookies.set("access_token", token)
    response = await test_client.get("/sales?sort_by=monthly_revenue&order=asc")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio(loop_scope="function")
async def test_get_sales_expired_token(test_client):
    """GET /sales with expired token → 401."""
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    expired_token = jwt.encode(
        {"sub": settings.ADMIN_USERNAME, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    test_client.cookies.set("access_token", expired_token)
    response = await test_client.get("/sales")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
