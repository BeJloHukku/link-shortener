from typing import Protocol

from links.domain.exceptions import SlugAlreadyExistError


class LinkRepository(Protocol):
    async def add(
        self,
        slug: str,
        long_url: str,
        exception: type[Exception] = SlugAlreadyExistError,
    ) -> None: ...

    async def get_long_url(self, slug: str) -> str | None: ...
