from redis.asyncio import Redis

from links.application.dto import (
    CachedLinkDTO,
    LinkWithSlugDTO,
)
from links.domain.config import LinkExpirationPolicy


class RedisCacheRepository:
    def __init__(self, redis: Redis):
        self._redis = redis
        self._ttl = LinkExpirationPolicy.MAX_TTL_SECONDS

    async def save_link(self, link_dto: LinkWithSlugDTO) -> None:
        slug = link_dto.slug
        origin_url = link_dto.origin_url

        await self._redis.set(
            name=f"link:{slug}",
            value=origin_url,
            ex=self._ttl,
        )

    async def get_and_refresh_link(self, slug: str) -> CachedLinkDTO | None:
        key = f"link:{slug}"
        async with self._redis.pipeline() as pipe:
            pipe.ttl(key)
            pipe.getex(key, ex=self._ttl)
            ttl, origin_url = await pipe.execute()

        if origin_url is None:
            return None
        return CachedLinkDTO(
            ttl=ttl,
            origin_url=origin_url,
        )
