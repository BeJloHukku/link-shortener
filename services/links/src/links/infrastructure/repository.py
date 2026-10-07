from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from links.domain.exceptions import LinkAlreadyExistError
from links.infrastructure.models import ShortUrl


async def add_slug_to_datebase(
    slug: str,
    long_url: str,
    session: AsyncSession,
):
    new_slug = ShortUrl(
        slug=slug,
        long_url=long_url,
    )
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
    return res.long_url if res else None


class SqlAlchemyLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        slug: str,
        long_url: str,
    ) -> None:
        await add_slug_to_datebase(
            slug,
            long_url,
            self.session,
        )

    async def get_long_url(self, slug: str) -> str | None:
        return await get_long_url_by_slug_from_database(slug, self.session)
