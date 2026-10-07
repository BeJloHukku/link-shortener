from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
)


class LinkSchema(BaseModel):
    origin_url: HttpUrl


class CustomLinkScheme(LinkSchema):
    custom_url: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
