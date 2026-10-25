from datetime import (
    UTC,
    datetime,
    timedelta,
)

import pytest

from links.application.dto import LinkAccessDTO
from links.infrastructure.db.models import ShortUrl

pytestmark = pytest.mark.integration

BASE_TIME = datetime(2026, 1, 1, 12, 0)
NEWER = BASE_TIME.replace(tzinfo=UTC) + timedelta(hours=1)
OLDER = BASE_TIME.replace(tzinfo=UTC) - timedelta(hours=1)

FAKE_LINK_SLUG = "test-slug"
FAKE_ORIGIN_URL = "https://test-origin-url"


async def test_expired_link(repository):
    await repository.add(
        slug=FAKE_LINK_SLUG,
        origin_url=FAKE_ORIGIN_URL,
        last_accessed_at=datetime.now() - timedelta(days=30),
    )

    expired_link = await repository.get_long_url(slug=FAKE_LINK_SLUG)
    assert expired_link is None


async def test_touch_return_false_with_unknown_slug(repository):
    link = LinkAccessDTO(
        slug=FAKE_LINK_SLUG,
        accessed_at=NEWER,
    )

    res = await repository.touch(link)

    assert not res


async def test_touch_not_updates_with_older_event(repository, session):
    await repository.add(
        slug=FAKE_LINK_SLUG,
        origin_url=FAKE_ORIGIN_URL,
        last_accessed_at=BASE_TIME,
    )

    link = LinkAccessDTO(
        slug=FAKE_LINK_SLUG,
        accessed_at=OLDER,
    )

    res = await repository.touch(link)
    assert not res

    link_from_db = await session.get(
        ShortUrl,
        FAKE_LINK_SLUG,
        populate_existing=True,
    )
    assert link_from_db.last_accessed_at == BASE_TIME


async def test_touch_updates_with_newer_event(repository, session):
    await repository.add(
        slug=FAKE_LINK_SLUG,
        origin_url=FAKE_ORIGIN_URL,
        last_accessed_at=BASE_TIME,
    )

    link = LinkAccessDTO(
        slug=FAKE_LINK_SLUG,
        accessed_at=NEWER,
    )

    res = await repository.touch(link)
    assert res

    link_from_db = await session.get(
        ShortUrl,
        FAKE_LINK_SLUG,
        populate_existing=True,
    )
    assert link_from_db.last_accessed_at == NEWER.replace(tzinfo=None)
