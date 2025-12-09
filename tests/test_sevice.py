from httpx import AsyncClient
from pydantic import HttpUrl
import pytest

from src.exeptions import CusomUrlAlreadyExistError, WrongUrlGivenError
from src.service import generate_custom_link, generate_short_url, get_url_by_slug
from src.datebase.crud import get_long_url_by_slug_from_database

async def test_generate_short_url(session):
    result = await generate_short_url("https://google.com", session)
    assert type(result) is str
    assert len(result) == 6

async def test_generate_short_url_already_exist(session):
    pass

async def test_generate_short_url_wrong_url_error(session):
    with pytest.raises(WrongUrlGivenError):
        await generate_short_url("not-a-url", session)

async def test_generate_custom_link(session):
    class CustomLinkData:
        origin_url = HttpUrl("https://google.com/")
        custom_url = "mylink"

    result = await generate_custom_link(CustomLinkData(), session)
    assert type(result) is str
    assert result == "mylink"
    
    long_url = await get_long_url_by_slug_from_database(result, session)
    assert long_url == "https://google.com/"

async def test_generate_custom_link_already_exist_error(session):
    class CustomLinkData:
        origin_url = HttpUrl("https://google.com/")
        custom_url = "repeat"
    
    await generate_custom_link(CustomLinkData(), session)

    with pytest.raises(CusomUrlAlreadyExistError):
        await generate_custom_link(CustomLinkData(), session)
    

async def test_get_url_by_slug(session):
    slug = await generate_short_url("https://google.com", session)
    result = await get_url_by_slug(slug, session)
    assert result == "https://google.com"


async def test_get_url_by_custom(session):
    class CustomLinkData:
        origin_url = HttpUrl("https://google.com/")
        custom_url = "google"
    custom_link = await generate_custom_link(CustomLinkData(), session)
    result = await get_url_by_slug(custom_link, session)
    assert result == "https://google.com/"


