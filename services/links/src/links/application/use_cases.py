import logging
from datetime import datetime

from links.application.dto import (
    LinkAccessDTO,
    LinkWithSlugDTO,
)
from links.application.exceptions import BrokerUnavailableError
from links.application.ports import (
    CacheRepository,
    LinkRepository,
    MessageBroker,
)
from links.application.retry import retry
from links.domain.config import LinkExpirationPolicy
from links.domain.exceptions import (
    NoLongUrlFoundError,
    SlugAlreadyExistError,
)
from links.domain.shortener import generate_random_slug
from links.domain.validation import validate_url

logger = logging.getLogger(__name__)


@retry(times=10, exception=SlugAlreadyExistError)
async def generate_short_url(
    origin_url: str,
    repository: LinkRepository,
) -> str:
    validate_url(origin_url)
    slug = generate_random_slug()
    await repository.add(slug, origin_url)
    return slug


async def generate_custom_link(
    data,
    repository: LinkRepository,
) -> str:
    origin_url = str(data.origin_url)
    custom_url = data.custom_url
    validate_url(origin_url)
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
        cached_link = await self.cache.get_link(slug)

        if cached_link is not None:
            if cached_link.ttl < LinkExpirationPolicy.UPDATE_THRESHOLD_SEC:
                if await self._notify_access(slug):
                    await self.cache.refresh_ttl(slug)
            return cached_link.origin_url

        origin_url = await self.db.get_long_url(slug)

        if origin_url is None:
            raise NoLongUrlFoundError()

        link_dto = LinkWithSlugDTO(slug=slug, origin_url=origin_url)
        await self.cache.save_link(link_dto)

        await self._notify_access(slug)

        return origin_url

    async def _notify_access(self, slug: str) -> bool:
        try:
            await self.broker.publish_accessed_link_event(slug)
        except BrokerUnavailableError:
            logger.warning(
                "Брокер недоступен, событие link.accessed для slug=%s не отправлено", slug
            )
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Не удалось опубликовать link.accessed для slug=%s", slug)
        else:
            return True
        return False


class RecordLinkAccessUseCase:
    def __init__(
        self,
        db: LinkRepository,
    ):
        self.db = db

    async def execute(
        self,
        slug: str,
        accessed_at: datetime,
    ) -> bool:
        link = LinkAccessDTO(
            slug=slug,
            accessed_at=accessed_at,
        )

        return await self.db.touch(link)
