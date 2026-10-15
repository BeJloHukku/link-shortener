from typing import Protocol
from links.application.dto import CachedLinkDTO, LinkWithSlugDTO


class LinkRepository(Protocol):
    async def add(
        self,
        slug: str,
        origin_url: str,
    ) -> None: ...

    async def get_long_url(self, slug: str) -> str | None: ...


class CacheRepository(Protocol):
    async def save_link(self, link_dto: LinkWithSlugDTO) -> None: ...

    async def get_and_refresh_link(self, slug: str) -> CachedLinkDTO | None: ...


class MessageBroker(Protocol):
    async def publish_accessed_link_event(self, slug: str) -> None: ...
