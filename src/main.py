from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from pydantic import BaseModel, HttpUrl, Field

from fastapi import Depends, FastAPI, Body, HTTPException, status
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.datebase.db import engine, new_session
from src.datebase.models import Base

from sqlalchemy.ext.asyncio import AsyncSession

from src.exeptions import CusomUrlAlreadyExistError, NoLongUrlFoundError, SlugAlreadyExistError, WrongUrlGivenError
from src.service import generate_custom_link, generate_short_url, get_url_by_slug

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

class CustomLinkScheme(BaseModel):
    origin_url: HttpUrl
    custom_url: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with new_session() as session:
        yield session


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/shorten_url")
async def generate_slug(
    long_url: Annotated[str, Body(embed=True)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        new_slug = await generate_short_url(long_url, session)
    except SlugAlreadyExistError:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Не удалось сжать ссылку. Попробуйте позже!"
        )
    except WrongUrlGivenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Неверный формат ввода!")
    return {"data": new_slug}

@app.post("/custom_url")
async def create_custom_link(
    data: CustomLinkScheme,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        custom_link = await generate_custom_link(data, session)
        return {"data": custom_link}
    except WrongUrlGivenError:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Неверный формат ввода!",
        )
    except CusomUrlAlreadyExistError:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Такая ссылка уже существует! Попробуйте ввести другую!"
        )

@app.get("/{slug}")
async def redirect_to_origin(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    try:
        long_url = await get_url_by_slug(slug, session)
    except NoLongUrlFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не существует")
    return RedirectResponse(url=long_url, status_code=status.HTTP_302_FOUND)