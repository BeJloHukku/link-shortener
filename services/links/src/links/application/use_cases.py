from links.application.ports import LinkRepository, CacheRepository, MessageBroker
from links.application.retry import retry
from links.application.dto import LinkWithSlugDTO
from links.application.config import RedirectWorkerConfig
from links.domain.exceptions import (
    NoLongUrlFoundError,
    SlugAlreadyExistError,
    WrongUrlGivenError,
)
from links.domain.shortener import generate_random_slug
from links.domain.validation import validate_url


@retry(times=10, exception=SlugAlreadyExistError)
async def generate_short_url(
    long_url: str,
    repository: LinkRepository,
) -> str:
    try:
        validate_url(long_url)
    except WrongUrlGivenError:
        raise WrongUrlGivenError
    slug = generate_random_slug()
    await repository.add(slug, long_url)
    return slug


async def generate_custom_link(
    data,
    repository: LinkRepository,
) -> str:
    origin_url = str(data.origin_url)
    custom_url = data.custom_url
    try:
        validate_url(origin_url)
    except WrongUrlGivenError:
        raise WrongUrlGivenError
    await repository.add(custom_url, origin_url)
    return custom_url


class GetRedirectUseCase:
    def __init__(
        self,
        db: LinkRepository,
        cache: CacheRepository,
        broker: MessageBroker,
    ) -> None:
        self.db = db
        self.cache = cache
        self.broker = broker

    async def execute(self, slug: str) -> str:
        cached_link = await self.cache.get_and_refresh_link(slug)

        if cached_link is not None:
            if cached_link.ttl < RedirectWorkerConfig.UPDATE_THRESHOLD_SEC:
                await self.broker.publish_accessed_link_event(slug)
            return cached_link.origin_url

        origin_url = await self.db.get_long_url(slug)

        if origin_url is None:
            raise NoLongUrlFoundError()

        link_dto = LinkWithSlugDTO(slug=slug, origin_url=origin_url)
        await self.cache.save_link(link_dto)

        await self.broker.publish_accessed_link_event(slug)

        return origin_url
