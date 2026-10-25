from typing import (
    AsyncGenerator,
    NamedTuple,
)
from unittest.mock import create_autospec
from urllib.parse import quote

import aio_pika
import pytest
from aio_pika.abc import (
    AbstractExchange,
    AbstractQueue,
)
from httpx import (
    ASGITransport,
    AsyncClient,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.rabbitmq import RabbitMqContainer
from testcontainers.community.redis import RedisContainer

from links.api.dependencies import (
    get_broker,
    get_cache_repository,
    get_session,
)
from links.application.ports import (
    CacheRepository,
    LinkRepository,
    MessageBroker,
)
from links.application.use_cases import GetRedirectUseCase
from links.infrastructure.broker.rabbitmq_settings import (
    LAST_ACCESSED_DLQ,
    declare_topology,
)
from links.infrastructure.db.models import Base
from links.infrastructure.db.repository import SqlAlchemyLinkRepository
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


@pytest.fixture()
async def session():
    async with new_session() as session:
        yield session


@pytest.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def repository(session):

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


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7") as container:
        yield container


@pytest.fixture()
async def redis_client(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    async with Redis(host=host, port=port, decode_responses=True) as client:
        yield client
        await client.flushdb()


@pytest.fixture(scope="session")
def rabbitmq_container():
    with RabbitMqContainer("rabbitmq:4.1-management") as container:
        yield container


@pytest.fixture(scope="session")
def amqp_url(rabbitmq_container: RabbitMqContainer):
    c = rabbitmq_container
    host = c.get_container_host_ip()
    port = c.get_exposed_port(c.port)
    vhost = quote(c.vhost, safe="")

    return f"amqp://{c.username}:{c.password}@{host}:{port}/{vhost}"


class RabbitMQ(NamedTuple):
    exchange: AbstractExchange
    queue: AbstractQueue
    dlq: AbstractQueue


@pytest.fixture()
async def rabbitmq(amqp_url: str):
    async with await aio_pika.connect_robust(url=amqp_url) as connection:
        channel = await connection.channel()
        exchange, queue = await declare_topology(channel)
        dlq = await channel.get_queue(LAST_ACCESSED_DLQ)

        yield RabbitMQ(
            exchange=exchange,
            queue=queue,
            dlq=dlq,
        )

        await queue.delete()
        await dlq.delete()
        await exchange.delete()
