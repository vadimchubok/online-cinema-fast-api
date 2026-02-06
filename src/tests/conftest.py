import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.database import get_async_session, Base
from src.main import app
from src.core.config import settings
from unittest.mock import MagicMock
import boto3


test_engine = create_async_engine(settings.database_url_async, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_db


@pytest.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_s3_client(monkeypatch):
    mock_s3 = MagicMock()
    def get_mock_client(*args, **kwargs):
        return mock_s3

    monkeypatch.setattr(boto3, "client", get_mock_client)
    return mock_s3
