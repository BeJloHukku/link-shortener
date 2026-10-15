import asyncio

import pytest
from redis.asyncio import Redis
from links.domain.config import LinkExpirationPolicy
from links.application.dto import LinkWithSlugDTO
from links.infrastructure.cache.redis import RedisCacheRepository

pytestmark = [pytest.mark.docker, pytest.mark.integration]

FAKE_ORIGIN_URL = "origin_url"
FAKE_SLUG = "slug"
REDIS_LINK_PREFIX = "link"
REDIS_LINK = f"{REDIS_LINK_PREFIX}:{FAKE_SLUG}"
FAKE_LINK = LinkWithSlugDTO(
    origin_url=FAKE_ORIGIN_URL,
    slug=FAKE_SLUG,
)
TIMEDELTA_SECONDS = 10

async def test_cache_save_link(redis_client: Redis):
    repo = RedisCacheRepository(redis=redis_client)
    link = FAKE_LINK
    await repo.save_link(link)
    cached_link = await redis_client.get(f'{REDIS_LINK}')
    ttl = await redis_client.ttl(f'{REDIS_LINK}')

    assert cached_link == FAKE_ORIGIN_URL
    assert 0 < ttl <= LinkExpirationPolicy.MAX_TTL_SECONDS


async def test_cache_get_link(redis_client: Redis):
    repo = RedisCacheRepository(redis=redis_client)
    link = FAKE_LINK
    await repo.save_link(link)
    link = await repo.get_and_refresh_link(link.slug)

    assert link is not None
    assert link.origin_url == FAKE_ORIGIN_URL


async def test_cache_get_link_not_found(redis_client: Redis):
    repo = RedisCacheRepository(redis=redis_client)
    link = FAKE_LINK
    await repo.save_link(link)
    link = await repo.get_and_refresh_link("not-found")

    assert link is None


async def test_cache_get_link_and_refresh(redis_client: Redis):
    repo = RedisCacheRepository(redis=redis_client)
    link = FAKE_LINK
    await repo.save_link(link)
    await  redis_client.expire(
        name=REDIS_LINK,
        time=100,
    )

    cached_link = await repo.get_and_refresh_link(link.slug)
    assert cached_link is not None
    previous_ttl = cached_link.ttl
    assert previous_ttl <= 100
    current_ttl = await redis_client.ttl(f'{REDIS_LINK}')
    start = LinkExpirationPolicy.MAX_TTL_SECONDS - TIMEDELTA_SECONDS
    end = LinkExpirationPolicy.MAX_TTL_SECONDS
    assert start <= current_ttl <= end


async def test_cache_get_link_expired(redis_client: Redis):
    repo = RedisCacheRepository(redis=redis_client)
    link = FAKE_LINK
    await repo.save_link(link)
    await redis_client.pexpire(
        name=REDIS_LINK,
        time=10,
    )
    await asyncio.sleep(0.2)
    cached_link = await repo.get_and_refresh_link(link.slug)
    assert cached_link is None

