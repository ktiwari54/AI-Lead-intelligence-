import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_docs_available(client: AsyncClient):
    response = await client.get("/api/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema(client: AsyncClient):
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AI Lead Intelligence Platform"
    assert "/api/v1/auth/register" in schema["paths"]
    assert "/api/v1/companies/" in schema["paths"]
    assert "/api/v1/contacts/" in schema["paths"]
    assert "/api/v1/search/" in schema["paths"]
