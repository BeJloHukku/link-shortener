from httpx import AsyncClient
from pydantic import HttpUrl

from src.service import generate_custom_link, generate_short_url
from src.datebase.crud import get_long_url_by_slug_from_database

async def test_generate_short_url(session):
    result = await generate_short_url("https://google.com", session)
    assert type(result) is str
    assert len(result) == 6

async def test_generate_short_url_already_exist(session):
    pass

async def test_generate_custom_link(session):
    class CustomLinkData:
        origin_url = HttpUrl("https://google.com")
        custom_url = "mylink"

    result = await generate_custom_link(CustomLinkData(), session)
    assert type(result) is str
    assert result == "mylink"
    
    long_url = await get_long_url_by_slug_from_database(result, session)
    assert long_url == "https://google.com/"