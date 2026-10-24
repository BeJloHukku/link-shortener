import json
from datetime import datetime, UTC
import logging
import uuid

from aio_pika import Message, DeliveryMode
from aio_pika.abc import AbstractRobustExchange

from links.application.events import LinkAccessedEvent

logger = logging.getLogger(__name__)


LINK_ACCESSED_ROUTING_KEY = "link.accessed"


class NullBroker:
    async def publish_accessed_link_event(self, slug: str) -> None:
        logger.warning("Брокер не подключён, событие link.accessed для %s не отправлено", slug)


class RabbitMQBroker:
    def __init__(self, exchange: AbstractRobustExchange) -> None:
        self._exchange = exchange

    async def publish_accessed_link_event(self, slug: str) -> None:
        event = LinkAccessedEvent(
            event_id=uuid.uuid4(),
            event_type="link.accessed",
            version=1,
            slug=slug,
        )

        message = Message(
            body=event.model_dump_json().encode("utf-8"),
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=str(event.event_id),
            type="link.accessed",
        )

        await self._exchange.publish(
            message=message,
            routing_key=LINK_ACCESSED_ROUTING_KEY,
            timeout=1.0,
        )
