from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from links.application.ports import LinkRepository
from links.infrastructure.db import new_session
from links.infrastructure.repository import SqlAlchemyLinkRepository


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with new_session() as session:
        yield session


def get_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LinkRepository:
    return SqlAlchemyLinkRepository(session)
