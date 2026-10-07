from typing import (
    Annotated,
    AsyncGenerator,
)

from aio_pika.abc import AbstractRobustChannel
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from links.application.ports import LinkRepository, CacheRepository, MessageBroker
from links.application.use_cases import GetRedirectUseCase
from links.infrastructure.rabbitmq import get_rabbitmq_channel
from links.infrastructure.rabbitmq_broker import RabbitMQBroker
from links.infrastructure.db import new_session
from links.infrastructure.redis_cache import RedisCacheRepository
from links.infrastructure.repository import SqlAlchemyLinkRepository
from links.infrastructure.redis import get_redis_client


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with new_session() as session:
        yield session


def get_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LinkRepository:
    return SqlAlchemyLinkRepository(session)


def get_broker(
    channel: Annotated[AbstractRobustChannel, Depends(get_rabbitmq_channel)],
) -> MessageBroker:
    return RabbitMQBroker(channel)


def get_cache_repository(redis: Annotated[Redis, Depends(get_redis_client)]) -> CacheRepository:
    return RedisCacheRepository(redis)


def get_redirect_use_case(
    db: Annotated[LinkRepository, Depends(get_repository)],
    cache: Annotated[CacheRepository, Depends(get_cache_repository)],
    broker: Annotated[MessageBroker, Depends(get_broker)],
) -> GetRedirectUseCase:
    return GetRedirectUseCase(
        db=db,
        cache=cache,
        broker=broker,
    )
