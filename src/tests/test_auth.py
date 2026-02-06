import pytest
from httpx import AsyncClient
from sqlalchemy import update
from src.auth.models import User


@pytest.mark.integration
async def test_register_user_success(client: AsyncClient):
    payload = {"email": "testuser@example.com", "password": "Strongpassword123!"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == payload["email"]


@pytest.mark.integration
async def test_register_user_duplicate_email(client: AsyncClient):
    payload = {"email": "duplicate@example.com", "password": "Password123!"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


@pytest.mark.integration
async def test_login_success(client: AsyncClient, db_session):
    email, password = "login@test.com", "Pass123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    await db_session.execute(update(User).where(User.email == email).values(is_active=True))
    await db_session.commit()

    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.integration
async def test_get_me_success(client: AsyncClient, db_session):
    email, password = "me@test.com", "Pass123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    await db_session.execute(update(User).where(User.email == email).values(is_active=True))
    await db_session.commit()

    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == email


@pytest.mark.integration
async def test_refresh_token_success(client: AsyncClient, db_session):
    email, password = "ref@test.com", "Pass123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    await db_session.execute(update(User).where(User.email == email).values(is_active=True))
    await db_session.commit()

    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    refresh_token = login_res.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()
