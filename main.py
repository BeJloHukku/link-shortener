from contextlib import asynccontextmanager

from fastapi import FastAPI, Body

from datebase.db import engine
from datebase.models import Base

from service import generate_short_url

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)


@app.post("/shorten_url")
async def generate_slug(
    long_url: str = Body(embed=True),
):
    new_slug = await generate_short_url(long_url)
    return {"data": new_slug}


@app.get("/{slug}")
async def redirect_to_origin(slug: str):
    return ...