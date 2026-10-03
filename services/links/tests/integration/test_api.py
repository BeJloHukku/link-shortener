from httpx import AsyncClient


async def test_generate_slug(ac: AsyncClient):
    result = await ac.post("/shorten_url", json={"long_url": "https://vk.com"})
    assert result.status_code == 200

async def test_redirect_to_origin(ac: AsyncClient):
    create_result = await ac.post("/shorten_url", json={"long_url": "https://vk.com"})
    assert create_result.status_code == 200
    
    short_url = create_result.json()["data"]
    slug = short_url.split("/")[-1]
    
    result = await ac.get(f"/{slug}", follow_redirects=False)
    assert result.status_code == 302
    assert result.headers["location"] == "https://vk.com"

