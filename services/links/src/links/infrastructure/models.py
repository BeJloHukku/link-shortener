from datetime import datetime
from sqlalchemy.sql import func

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class ShortUrl(Base):
    __tablename__ = "short_urls"

    slug: Mapped[str] = mapped_column(primary_key=True)
    origin_url: Mapped[str]
    last_accessed_at: Mapped[datetime] = mapped_column(default=func.now())
