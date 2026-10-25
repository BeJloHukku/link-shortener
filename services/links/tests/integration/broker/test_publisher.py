from datetime import (
    UTC,
    datetime,
)

import pytest
from aio_pika import DeliveryMode
from tests.integration.broker.helpers import wait_message

from links.application.events import LinkAccessedEvent
from links.infrastructure.broker.rabbitmq import RabbitMQBroker

pytestmark = [pytest.mark.docker, pytest.mark.integration]

FAKE_SLUG = "fake-slug"


async def test_happy_path(rabbitmq):
    before = datetime.now(UTC)

    broker = RabbitMQBroker(exchange=rabbitmq.exchange)
    await broker.publish_accessed_link_event(slug=FAKE_SLUG)

    queue = rabbitmq.queue
    msg = await wait_message(queue)

    event = LinkAccessedEvent.model_validate_json(msg.body)

    assert event.slug == FAKE_SLUG
    assert msg.message_id == str(event.event_id)
    assert event.occurred_at.tzinfo is not None
    assert before < event.occurred_at < datetime.now(UTC)
    assert msg.content_type == "application/json"
    assert msg.delivery_mode == DeliveryMode.PERSISTENT


async def test_every_message_has_unique_id(rabbitmq):
    broker = RabbitMQBroker(rabbitmq.exchange)

    await broker.publish_accessed_link_event(slug=FAKE_SLUG)
    await broker.publish_accessed_link_event(slug=FAKE_SLUG)

    queue = rabbitmq.queue
    first_msg = await wait_message(queue)
    second_msg = await wait_message(queue)

    assert first_msg.message_id != second_msg.message_id
