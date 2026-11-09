import logging

import pytest

from links.application.dto import (
    CachedLinkDTO,
    LinkWithSlugDTO,
)
from links.application.exceptions import BrokerUnavailableError
from links.domain.config import LinkExpirationPolicy
from links.domain.exceptions import NoLongUrlFoundError
from links.infrastructure.broker.rabbitmq import NullBroker

pytestmark = pytest.mark.integration

SLUG = "example"
ORIGIN_URL = "https://example.com/"
THRESHOLD = LinkExpirationPolicy.UPDATE_THRESHOLD_SEC


@pytest.mark.parametrize("ttl", [THRESHOLD, THRESHOLD + 1, LinkExpirationPolicy.MAX_TTL_SECONDS])
async def test_recent_cache_hit_does_not_publish_or_refresh(
    ttl, redirect_use_case, mock_cache, mock_broker
):
    mock_cache.get_link.return_value = CachedLinkDTO(origin_url=ORIGIN_URL, ttl=ttl)

    assert await redirect_use_case.execute(SLUG) == ORIGIN_URL

    mock_cache.get_link.assert_awaited_once_with(SLUG)
    mock_broker.publish_accessed_link_event.assert_not_awaited()
    mock_cache.refresh_ttl.assert_not_awaited()
    mock_cache.save_link.assert_not_awaited()


@pytest.mark.parametrize("ttl", [THRESHOLD - 1, 0])
async def test_old_cache_hit_publishes_before_refreshing(
    ttl, redirect_use_case, mock_cache, mock_broker
):
    mock_cache.get_link.return_value = CachedLinkDTO(origin_url=ORIGIN_URL, ttl=ttl)

    async def check_published(slug):
        mock_broker.publish_accessed_link_event.assert_awaited_once_with(slug)

    mock_cache.refresh_ttl.side_effect = check_published

    assert await redirect_use_case.execute(SLUG) == ORIGIN_URL

    mock_cache.refresh_ttl.assert_awaited_once_with(SLUG)
    mock_cache.save_link.assert_not_awaited()


async def test_publish_failure_preserves_ttl_and_next_request_retries(
    redirect_use_case, mock_cache, mock_broker
):
    mock_cache.get_link.return_value = CachedLinkDTO(origin_url=ORIGIN_URL, ttl=THRESHOLD - 1)
    mock_broker.publish_accessed_link_event.side_effect = [RuntimeError("publish failed"), None]

    assert await redirect_use_case.execute(SLUG) == ORIGIN_URL
    mock_cache.refresh_ttl.assert_not_awaited()

    assert await redirect_use_case.execute(SLUG) == ORIGIN_URL
    assert mock_broker.publish_accessed_link_event.await_count == 2
    mock_cache.refresh_ttl.assert_awaited_once_with(SLUG)


async def test_null_broker_reports_failure():
    with pytest.raises(BrokerUnavailableError):
        await NullBroker().publish_accessed_link_event(SLUG)


async def test_null_broker_does_not_refresh_ttl(redirect_use_case, mock_cache, caplog):
    mock_cache.get_link.return_value = CachedLinkDTO(origin_url=ORIGIN_URL, ttl=THRESHOLD - 1)
    redirect_use_case.broker = NullBroker()

    with caplog.at_level(logging.WARNING, logger="links.application.redirect_use_cases"):
        assert await redirect_use_case.execute(SLUG) == ORIGIN_URL

    mock_cache.refresh_ttl.assert_not_awaited()
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == logging.WARNING
    assert record.exc_info is None
    assert SLUG in record.getMessage()


@pytest.mark.parametrize("publish_fails", [False, True])
async def test_cache_miss_saves_and_publishes(
    publish_fails, redirect_use_case, repository, mock_cache, mock_broker
):
    await repository.add(SLUG, ORIGIN_URL)

    async def check_saved(slug):
        mock_cache.save_link.assert_awaited_once_with(
            LinkWithSlugDTO(slug=slug, origin_url=ORIGIN_URL)
        )
        if publish_fails:
            raise RuntimeError("publish failed")

    mock_broker.publish_accessed_link_event.side_effect = check_saved

    assert await redirect_use_case.execute(SLUG) == ORIGIN_URL

    mock_broker.publish_accessed_link_event.assert_awaited_once_with(SLUG)
    mock_cache.refresh_ttl.assert_not_awaited()


async def test_missing_link_does_not_save_publish_or_refresh(
    redirect_use_case, mock_cache, mock_broker
):
    with pytest.raises(NoLongUrlFoundError):
        await redirect_use_case.execute(SLUG)

    mock_cache.save_link.assert_not_awaited()
    mock_cache.refresh_ttl.assert_not_awaited()
    mock_broker.publish_accessed_link_event.assert_not_awaited()
