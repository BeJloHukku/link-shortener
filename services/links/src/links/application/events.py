from datetime import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, Field


class LinkAccessedEvent(BaseModel):
    event_id: uuid.UUID

    event_type: Literal["link.accessed"]

    version: Literal[1]

    slug: str

    occurred_at: datetime = Field(default_factory=datetime.now)
