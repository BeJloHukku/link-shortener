from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class ShortUrl(Base):
    __tablename__ = "short_urls"

    slug: Mapped[str] = mapped_column(primary_key=True)
    long_url: Mapped[str]