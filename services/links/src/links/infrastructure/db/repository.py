from datetime import datetime, timedelta

from sqlalchemy import select
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
