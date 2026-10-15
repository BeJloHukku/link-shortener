import pytest
from pydantic import HttpUrl

from links.application.use_cases import (
    generate_custom_link,
    generate_short_url,
)
from links.domain.exceptions import (
    LinkAlreadyExistError,
    WrongUrlGivenError,
)
from links.infrastructure.db.repository import get_long_url_by_slug_from_database


pytestmark = pytest.mark.integration


async def test_generate_short_url(session, repository):
    result = await generate_short_url("https://google.com", repository)
    assert type(result) is str
    assert len(result) == 6


async def test_generate_short_url_wrong_url_error(session, repository):
    with pytest.raises(WrongUrlGivenError):
        await generate_short_url("not-a-url", repository)


async def test_generate_custom_link(session, repository):
    class CustomLinkData:
        origin_url = HttpUrl("https://google.com/")
        custom_url = "mylink"

    result = await generate_custom_link(CustomLinkData(), repository)
    assert type(result) is str
    assert result == "mylink"

    origin_url = await get_long_url_by_slug_from_database(result, session)
    assert origin_url == "https://google.com/"


async def test_generate_custom_link_already_exist_error(session, repository):
    class CustomLinkData:
        origin_url = HttpUrl("https://google.com/")
        custom_url = "repeat"

    await generate_custom_link(CustomLinkData(), repository)

    with pytest.raises(LinkAlreadyExistError):
        await generate_custom_link(CustomLinkData(), repository)


async def test_get_url_by_slug(
    session,
    repository,
    mock_cache,
    mock_broker,
    redirect_use_case,
):
    slug = await generate_short_url("https://google.com", repository)
    result = await redirect_use_case.execute(slug)
    assert result == "https://google.com"

    mock_cache.save_link.assert_called_once()
    mock_broker.publish_accessed_link_event.assert_called_once()


async def test_get_url_by_custom(
    session,
    repository,
    mock_cache,
    mock_broker,
    redirect_use_case,
):
    class CustomLinkData:
        origin_url = HttpUrl("https://google.com/")
        custom_url = "google"

    custom_link = await generate_custom_link(CustomLinkData(), repository)
    result = await redirect_use_case.execute(custom_link)
    assert result == "https://google.com/"

    mock_cache.save_link.assert_called_once()
    mock_broker.publish_accessed_link_event.assert_called_once()
