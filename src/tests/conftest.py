import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import asyncio
import boto3
from unittest.mock import MagicMock
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import insert, select
from sqlalchemy.pool import StaticPool

from src.core.database import Base, get_async_session
from src.main import app
from src.auth.models import User, UserGroup, UserGroupEnum
from src.auth.security import create_access_token

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


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
        session.add_all(
            [
                UserGroup(name=UserGroupEnum.USER.value),
                UserGroup(name=UserGroupEnum.MODERATOR.value),
                UserGroup(name=UserGroupEnum.ADMIN.value),
            ]
        )
        await session.commit()
    yield


@pytest.fixture(scope="function", autouse=True)
def mock_external_services(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("redis.asyncio.from_url", lambda *args, **kwargs: mock)
    monkeypatch.setattr("src.auth.router.send_email", lambda *args, **kwargs: None)

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime.now().replace(tzinfo=None)

    monkeypatch.setattr("src.auth.router.datetime", FakeDatetime)
    return mock


@pytest.fixture
def mock_s3_client(monkeypatch):
    mock_s3 = MagicMock()
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: mock_s3)
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
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def moderator_user(db_session):
    res = await db_session.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.MODERATOR.value)
    )
    group = res.scalar_one()

    stmt = (
        insert(User)
        .values(
            email="moderator@cinema.com",
            hashed_password="hashed_password",
            group_id=group.id,
            is_active=True,
        )
        .returning(User.id)
    )

    user_id = (await db_session.execute(stmt)).scalar()
    await db_session.commit()
    return user_id


@pytest.fixture
async def moderator_client(client, moderator_user):
    token = create_access_token(moderator_user)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
