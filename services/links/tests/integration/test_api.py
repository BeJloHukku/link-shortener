from httpx import AsyncClient


async def test_root(ac: AsyncClient):
    result = await ac.get("/")
    assert result.status_code == 200
    assert result.json() == {"status": "ok"}


async def test_invalid_url_with_shorten(ac: AsyncClient):
    result = await ac.post(
        "/shorten_url",
        json={"long_url": "invalid_url"},
    )
    assert result.status_code == 422
    assert result.json()["detail"] == "Неверный формат ввода!"


async def test_create_custom_link(ac: AsyncClient):
    result = await ac.post(
        "/custom_url",
        json={
            "origin_url": "https://vk.com",
            "custom_url": "custom",
        },
    )
    assert result.status_code == 200
    result_data = result.json()
    assert result_data["data"] == "custom"

    custom_url = result_data["data"]

    result = await ac.get(f"/{custom_url}", follow_redirects=False)
    assert result.status_code == 302
    assert result.headers["location"] == "https://vk.com/"


async def test_create_custom_link_with_conflict(ac: AsyncClient):
    await ac.post(
        "/custom_url",
        json={
            "origin_url": "https://vk.com",
            "custom_url": "custom",
        },
    )

    result = await ac.post(
        "/custom_url",
        json={
            "origin_url": "https://vk.com",
            "custom_url": "custom",
        },
    )
    assert result.status_code == 409
    assert result.json()["detail"] == "Такая ссылка уже существует! Попробуйте ввести другую!"


async def test_invalid_url_with_custom_shorten(ac: AsyncClient):
    result = await ac.post(
        "/custom_url",
        json={
            "origin_url": "www.google.com",
            "custom_url": "custom",
        },
    )
    assert result.status_code == 422
    assert result.json()["detail"] == "Неверный формат ввода!"


async def test_generate_slug(ac: AsyncClient):
    result = await ac.post("/shorten_url", json={"origin_url": "https://vk.com"})
    assert result.status_code == 200


async def test_redirect_to_origin(ac: AsyncClient):
    create_result = await ac.post("/shorten_url", json={"origin_url": "https://vk.com"})
    assert create_result.status_code == 200

    short_url = create_result.json()["data"]

    result = await ac.get(f"/{short_url}", follow_redirects=False)
    assert result.status_code == 302
    assert result.headers["location"] == "https://vk.com/"


async def test_url_not_found(ac: AsyncClient):
    result = await ac.get("fake_url", follow_redirects=False)
    assert result.status_code == 404
    assert result.json()["detail"] == "Ссылка не существует"
