from datebase.db import new_session
from datebase.models import ShortUrl

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from exeptions import SlugAlreadyExistError

async def add_slug_to_datebase(
        slug: str,
        long_url: str,
):
    async with new_session() as session:
        new_slug = ShortUrl (
            slug=slug,
            long_url=long_url,
        )
        session.add(new_slug)
        try:
            await session.commit()
        except IntegrityError:
            raise SlugAlreadyExistError

async def get_long_url_by_slug_from_database(slug: str,):
    async with new_session() as session:
        query = select(ShortUrl).filter_by(slug=slug)
        result = await session.execute(query)
        res: ShortUrl | None = result.scalar_one_or_none()
        return res.long_url if res.long_url else None
    