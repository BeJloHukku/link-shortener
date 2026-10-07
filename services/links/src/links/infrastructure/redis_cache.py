from redis.asyncio import Redis

from links.application.dto import LinkWithSlugDTO, CachedLinkDTO


class RedisCacheRepository:
    def __init__(self, redis: Redis):
        pass

    async def save_link(self, link_dto: LinkWithSlugDTO) -> None:
        pass

    async def get_and_refresh_link(self, slug: str) -> CachedLinkDTO | None:
        pass
