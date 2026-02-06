import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_register_user_success(client: AsyncClient):
    payload = {
        "email": "testuser@example.com",
        "password": "Strongpassword123!",
    }

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data


@pytest.mark.integration
async def test_register_user_duplicate_email(client: AsyncClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
    }

    await client.post("/auth/register", json=payload)

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 400
