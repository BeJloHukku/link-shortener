from typing import AsyncGenerator
from unittest.mock import create_autospec

import pytest
from httpx import (
    ASGITransport,
    AsyncClient,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from links.api.dependencies import get_session, get_broker, get_cache_repository
from links.application.ports import CacheRepository, MessageBroker
from links.application.use_cases import GetRedirectUseCase
from links.infrastructure.models import Base
from links.main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(url=DATABASE_URL)

new_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_test_session() -> AsyncGenerator[AsyncSession]:
    async with new_session() as session:
        yield session


def get_test_broker():
    mock = create_autospec(MessageBroker, instance=True)
    return mock


def get_test_cache():
    mock = create_autospec(CacheRepository, instance=True)
    mock.get_and_refresh_link.return_value = None
    return mock


app.dependency_overrides[get_session] = get_test_session
app.dependency_overrides[get_broker] = get_test_broker
app.dependency_overrides[get_cache_repository] = get_test_cache


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(scope="function")
async def session():
    async with new_session() as session:
        yield session


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def repository(session):
    from links.infrastructure.repository import SqlAlchemyLinkRepository

    return SqlAlchemyLinkRepository(session)


@pytest.fixture()
def mock_cache():
    """Fixture for CacheRepository"""
    mock = create_autospec(CacheRepository, instance=True)
    mock.get_and_refresh_link.return_value = None
    return mock


@pytest.fixture()
def mock_broker():
    """Fixture for MessageBroker"""
    mock = create_autospec(MessageBroker, instance=True)
    return mock


@pytest.fixture()
def redirect_use_case(
    repository,
    mock_cache,
    mock_broker,
) -> GetRedirectUseCase:

    return GetRedirectUseCase(
        db=repository,
        cache=mock_cache,
        broker=mock_broker,
    )
