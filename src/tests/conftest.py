import pytest
import asyncio
import boto3
from unittest.mock import MagicMock
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

import src.auth.security as security
security.hash_password = lambda p: f"hashed_{p}"
security.verify_password = lambda p, h: True

from src.core.database import Base, get_async_session
from src.main import app
from src.auth.models import UserGroup, UserGroupEnum


test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        session.add(UserGroup(name=UserGroupEnum.USER.value))
        await session.commit()
    yield

@pytest.fixture(scope="function", autouse=True)
def mock_external_services(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("redis.asyncio.from_url", lambda *args, **kwargs: mock)
    monkeypatch.setattr("src.auth.router.send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.auth.models.validate_password_strength", lambda p: None)

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime.now().replace(tzinfo=None)

    monkeypatch.setattr("src.auth.router.datetime", FakeDatetime)
    return mock

@pytest.fixture
def mock_s3_client(monkeypatch):
    mock_s3 = MagicMock()
    def get_mock_client(*args, **kwargs):
        return mock_s3
    monkeypatch.setattr(boto3, "client", get_mock_client)
    return mock_s3

@pytest.fixture(scope="function")
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


async def override_get_async_session():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_async_session

@pytest.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
