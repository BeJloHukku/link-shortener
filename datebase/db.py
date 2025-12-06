from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "6532")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(
    url="postgresql+asyncpg://postgres:postgres@localhost:6532/postgres"
)

new_session = async_sessionmaker(bind=engine, expire_on_commit=False)



