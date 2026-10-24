import logging
import uuid

from aio_pika import (
    DeliveryMode,
    Message,
)
from aio_pika.abc import AbstractRobustExchange

from links.application.events import LinkAccessedEvent
from links.infrastructure.broker.rabbitmq_settings import LINK_ACCESSED_ROUTING_KEY

logger = logging.getLogger(__name__)

LINK_ACCESSED_EVENT_TYPE = "link.accessed"
LINK_ACCESSED_EVENT_VERSION = 1
LINK_ACCESSED_EVENT_PUBLISH_TIMEOUT = 1.0


class NullBroker:
    async def publish_accessed_link_event(self, slug: str) -> None:
        logger.warning("Брокер не подключён, событие link.accessed для %s не отправлено", slug)


class RabbitMQBroker:
    def __init__(self, exchange: AbstractRobustExchange) -> None:
        self._exchange = exchange

    async def publish_accessed_link_event(self, slug: str) -> None:
        event = LinkAccessedEvent(
            event_id=uuid.uuid4(),
            event_type=LINK_ACCESSED_EVENT_TYPE,
            version=LINK_ACCESSED_EVENT_VERSION,
            slug=slug,
        )

        message = Message(
            body=event.model_dump_json().encode("utf-8"),
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=str(event.event_id),
            type=LINK_ACCESSED_EVENT_TYPE,
        )

        await self._exchange.publish(
            message=message,
            routing_key=LINK_ACCESSED_ROUTING_KEY,
            timeout=LINK_ACCESSED_EVENT_PUBLISH_TIMEOUT,
        )
