from datetime import (
    datetime,
    timedelta,
    UTC,
)

from sqlalchemy import select, update, Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from links.domain.config import LinkExpirationPolicy
from links.domain.exceptions import LinkAlreadyExistError
from links.infrastructure.db.models import ShortUrl


async def add_slug_to_datebase(
    slug: str,
    origin_url: str,
    session: AsyncSession,
    last_accessed_at: datetime | None = None,
):
    new_slug = ShortUrl(
        slug=slug,
        origin_url=origin_url,
    )
    if last_accessed_at is not None:
        new_slug.last_accessed_at = last_accessed_at
    session.add(new_slug)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise LinkAlreadyExistError


async def get_long_url_by_slug_from_database(
    slug: str,
    session: AsyncSession,
):
    query = select(ShortUrl).filter_by(slug=slug)
    result = await session.execute(query)
    res: ShortUrl | None = result.scalar_one_or_none()
    if res is not None:
        last_access = res.last_accessed_at
        if datetime.now() - last_access < timedelta(days=LinkExpirationPolicy.MAX_TTL_DAYS):
            return res.origin_url
    return None


class SqlAlchemyLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        slug: str,
        origin_url: str,
        last_accessed_at: datetime | None = None,
    ) -> None:
        await add_slug_to_datebase(
            slug,
            origin_url,
            self.session,
            last_accessed_at,
        )

    async def get_long_url(self, slug: str) -> str | None:
        return await get_long_url_by_slug_from_database(slug, self.session)

    async def touch(self, slug: str, accessed_at: datetime) -> datetime | None:
        accessed_at = accessed_at.astimezone(UTC).replace(tzinfo=None)

        query = (
            update(ShortUrl)
            .where(ShortUrl.slug == slug and ShortUrl.last_accessed_at < accessed_at)
            .values(last_accessed_at=accessed_at)
            .returning(ShortUrl)
        )

        result = await self.session.execute(query)
        short_url = result.scalar_one_or_none()

        await self.session.commit()

        if short_url is not None:
            return short_url.last_accessed_at
        return None
