from datebase.db import new_session
from datebase.models import ShortUrl

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
        await session.commit()
