from datebase.crud import add_slug_to_datebase, get_long_url_by_slug_from_database
from exeptions import NoLongUrlFoundError, SlugAlreadyExistError, WrongUrlGivenError
from retry_decorator import retry
from shortener import generate_random_slug
from url_validator import validate_url

@retry(times=10, exception=SlugAlreadyExistError)
async def generate_short_url (
        long_url: str,
) -> str:
    try:
        validate_url(long_url)
    except WrongUrlGivenError:
        raise WrongUrlGivenError
    slug = generate_random_slug()
    await add_slug_to_datebase(slug, long_url)
    return slug

async def get_url_by_slug(slug: str) -> str:
    long_url = await get_long_url_by_slug_from_database(slug)
    if not long_url:
        raise NoLongUrlFoundError()
    return long_url
