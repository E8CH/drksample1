import pytest
from fastapi import status


@pytest.mark.asyncio(loop_scope="function")
async def test_health_check(test_client):
    """GET /health should return 200 OK with status: ok."""
    response = await test_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
