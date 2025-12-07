from httpx import ASGITransport, AsyncClient
from src.datebase.models import Base
from src.main import app, get_session

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import pytest

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    url=DATABASE_URL
)

new_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_test_session() -> AsyncGenerator[AsyncSession]:
    async with new_session() as session:
        yield session

app.dependency_overrides[get_session] = get_test_session

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.fixture(scope="function")
async def session():
    async with new_session() as session:
        yield session


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac