from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from links.settings import DATABASE_URL

engine = create_async_engine(url=DATABASE_URL)

new_session = async_sessionmaker(bind=engine, expire_on_commit=False)
