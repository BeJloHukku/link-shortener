from typing import Protocol


class LinkRepository(Protocol):
    async def add(
        self,
        slug: str,
        long_url: str,
    ) -> None: ...

    async def get_long_url(self, slug: str) -> str | None: ...
