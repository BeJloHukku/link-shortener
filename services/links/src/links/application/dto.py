from pydantic import (
    BaseModel,
    Field,
)


class LinkDTO(BaseModel):
    origin_url: str = Field(description="Original URL")


class CachedLinkDTO(LinkDTO):
    ttl: int = Field(description="TTL in seconds")


class LinkWithSlugDTO(LinkDTO):
    slug: str = Field(description="Shortened or customized slug")
