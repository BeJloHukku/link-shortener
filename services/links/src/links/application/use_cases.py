from links.application.ports import LinkRepository
from links.application.retry import retry
from links.domain.exceptions import (
    NoLongUrlFoundError,
    SlugAlreadyExistError,
    WrongUrlGivenError,
)
from links.domain.shortener import generate_random_slug
from links.domain.validation import validate_url


@retry(times=10, exception=SlugAlreadyExistError)
async def generate_short_url(long_url: str, repository: LinkRepository) -> str:
    try:
        validate_url(long_url)
    except WrongUrlGivenError:
        raise WrongUrlGivenError
    slug = generate_random_slug()
    await repository.add(slug, long_url)
    return slug


async def get_url_by_slug(slug: str, repository: LinkRepository) -> str:
    long_url = await repository.get_long_url(slug)
    if not long_url:
        raise NoLongUrlFoundError()
    return long_url


async def generate_custom_link(data, repository: LinkRepository) -> str:
    origin_url = str(data.origin_url)
    custom_url = data.custom_url
    try:
        validate_url(origin_url)
    except WrongUrlGivenError:
        raise WrongUrlGivenError
    await repository.add(custom_url, origin_url)
    return custom_url
