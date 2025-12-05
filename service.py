from datebase.crud import add_slug_to_datebase
from shortener import generate_random_slug


async def generate_short_url (
        long_url: str,
):
    slug = generate_random_slug()
    await add_slug_to_datebase(
        slug, long_url
    )
    return slug
