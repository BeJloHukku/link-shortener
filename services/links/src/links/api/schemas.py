from pydantic import BaseModel, HttpUrl, Field


class CustomLinkScheme(BaseModel):
    origin_url: HttpUrl
    custom_url: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
