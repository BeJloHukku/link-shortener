from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    url="postgresql+asyncpg://postgres:postgres@localhost:6532/postgres"
)

new_session = async_sessionmaker(bind=engine, expire_on_commit=False)



