from datetime import (
    datetime,
    timedelta,
)

import pytest

pytestmark = pytest.mark.integration


async def test_expired_link(repository):
    await repository.add(
        slug="test-slug",
        origin_url="https://test-origin-url",
        last_accessed_at=datetime.now() - timedelta(days=30),
    )

    expired_link = await repository.get_long_url(slug="test-slug")
    assert expired_link is None
