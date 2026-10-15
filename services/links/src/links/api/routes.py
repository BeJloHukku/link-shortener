from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import RedirectResponse


from links.api.dependencies import get_redirect_use_case
from links.application.use_cases import GetRedirectUseCase
from links.api.dependencies import get_repository
from links.api.schemas import CustomLinkScheme, LinkSchema
from links.application.ports import LinkRepository
from links.application.use_cases import (
    generate_custom_link,
    generate_short_url,
)
from links.domain.exceptions import (
    NoLongUrlFoundError,
    SlugAlreadyExistError,
    LinkAlreadyExistError,
)

router = APIRouter()


@router.get("/")
async def root():
    return {"status": "ok"}


@router.post("/shorten_url")
async def generate_slug(
    link: LinkSchema,
    repository: Annotated[LinkRepository, Depends(get_repository)],
):
    try:
        new_slug = await generate_short_url(str(link.origin_url), repository)
    except SlugAlreadyExistError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сжать ссылку. Попробуйте позже!",
        )
    return {"data": new_slug}


@router.post("/custom_url")
async def create_custom_link(
    data: CustomLinkScheme,
    repository: Annotated[LinkRepository, Depends(get_repository)],
):
    try:
        custom_link = await generate_custom_link(data, repository)
        return {"data": custom_link}
    except LinkAlreadyExistError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такая ссылка уже существует! Попробуйте ввести другую!",
        )


@router.get("/{slug}")
async def redirect_to_origin(
    slug: str,
    redirect_use_case: Annotated[GetRedirectUseCase, Depends(get_redirect_use_case)],
) -> RedirectResponse:
    try:
        origin_url = await redirect_use_case.execute(slug=slug)
    except NoLongUrlFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ссылка не существует",
        )
    return RedirectResponse(
        url=origin_url,
        status_code=status.HTTP_302_FOUND,
    )
