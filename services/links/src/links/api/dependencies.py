from typing import (
    Annotated,
    AsyncGenerator,
)

from fastapi import (
    Depends,
    Request,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from links.application.ports import (
    CacheRepository,
    LinkRepository,
    MessageBroker,
)
from links.application.use_cases import GetRedirectUseCase
from links.infrastructure.cache.redis import RedisCacheRepository
from links.infrastructure.cache.redis_settings import get_redis_client
from links.infrastructure.db.db import new_session
from links.infrastructure.db.repository import SqlAlchemyLinkRepository


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with new_session() as session:
        yield session


def get_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LinkRepository:
    return SqlAlchemyLinkRepository(session)


def get_broker(
    request: Request,
) -> MessageBroker:
    return request.app.state.broker


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
