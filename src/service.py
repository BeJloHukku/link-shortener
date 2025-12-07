from sqlalchemy.ext.asyncio import AsyncSession

from src.datebase.crud import add_slug_to_datebase, get_long_url_by_slug_from_database
from src.exeptions import CusomUrlAlreadyExistError, NoLongUrlFoundError, SlugAlreadyExistError, WrongUrlGivenError
from src.retry_decorator import retry
from src.shortener import generate_random_slug
from src.url_validator import validate_url

@retry(times=10, exception=SlugAlreadyExistError)
async def generate_short_url (
        long_url: str,
        session: AsyncSession
) -> str:
    try:
        validate_url(long_url)
    except WrongUrlGivenError:
        raise WrongUrlGivenError
    slug = generate_random_slug()
    await add_slug_to_datebase(
        slug, long_url, session
        )
    return slug

async def get_url_by_slug(slug: str, session: AsyncSession) -> str:
    long_url = await get_long_url_by_slug_from_database(slug, session)
    if not long_url:
        raise NoLongUrlFoundError()
    return long_url

async def generate_custom_link(data, session: AsyncSession) -> str:
    origin_url = str(data.origin_url)
    custom_url = data.custom_url
    try:
        validate_url(origin_url)
    except WrongUrlGivenError:
        raise WrongUrlGivenError
    try:
        await add_slug_to_datebase(custom_url, origin_url, session, CusomUrlAlreadyExistError)
        return custom_url
    except CusomUrlAlreadyExistError:
        raise CusomUrlAlreadyExistError
    