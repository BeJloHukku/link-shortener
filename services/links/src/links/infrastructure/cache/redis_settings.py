from typing import AsyncGenerator
from redis.asyncio import ConnectionPool, Redis
from links.settings import REDIS_URL


redis_pool = ConnectionPool.from_url(
    REDIS_URL,
    decode_responses=True,
)


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """Генератор, который выдает и корректно закрывает Redis-клиент."""
    redis = Redis(connection_pool=redis_pool)
    try:
        yield redis
    finally:
        await redis.aclose()
