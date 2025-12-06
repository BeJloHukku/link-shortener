from contextlib import asynccontextmanager

from pydantic import BaseModel, HttpUrl, Field

from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import RedirectResponse

from datebase.db import engine
from datebase.models import Base

from exeptions import NoLongUrlFoundError, SlugAlreadyExistError, WrongUrlGivenError
from service import generate_short_url, get_url_by_slug

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

class CustomLinkScheme(BaseModel):
    origin_url: HttpUrl
    custom_part: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")


@app.post("/shorten_url")
async def generate_slug(
    long_url: str = Body(embed=True),
):
    try:
        new_slug = await generate_short_url(long_url)
    except SlugAlreadyExistError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="Не удалось сжать ссылку. Попробуйте позже!")
    except WrongUrlGivenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Неверный формат ввода!")
    return {"data": new_slug}

@app.post("/custom_url")
async def create_custom_link():
    # TODO: реализовать логику создания кастомной ссылки
    pass 

@app.get("/{slug}")
async def redirect_to_origin(slug: str):
    try:
        long_url = await get_url_by_slug(slug)
    except NoLongUrlFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не существует")
    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)