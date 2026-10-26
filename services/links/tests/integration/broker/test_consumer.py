import asyncio
import json
from dataclasses import dataclass

import pytest
from tests.integration.broker.helpers import (
    count_messages,
    eventually,
    generate_link_accessed_event_json,
    publish_raw,
    wait_message,
)

from links.application.events import LinkAccessedEvent
from links.infrastructure.broker.consumer import LinkAccessedConsumer
from links.infrastructure.broker.rabbitmq import (
    LINK_ACCESSED_EVENT_TYPE,
    RabbitMQBroker,
)
from links.infrastructure.broker.rabbitmq_settings import LAST_ACCESSED_QUEUE

pytestmark = [pytest.mark.docker, pytest.mark.integration]

FAKE_SLUG = "fake-slug"


class FakeHandler:
    def __init__(self) -> None:
        self.events: list[LinkAccessedEvent] = []
        self.error = None
        self.release = asyncio.Event()
        self.release.set()

    async def __call__(self, event: LinkAccessedEvent) -> None:
        if self.error:
            raise self.error
        self.events.append(event)
        await self.release.wait()

    def set_error(self, error: Exception) -> None:
        self.error = error

    def lock_execution(self):
        self.release.clear()

    def unlock_execution(self):
        self.release.set()


async def test_happy_path(rabbitmq):
    handler = FakeHandler()
    publisher = RabbitMQBroker(rabbitmq.exchange)
    consumer = LinkAccessedConsumer(
        rabbitmq.queue,
        handler,
    )

    await consumer.start()
    await publisher.publish_accessed_link_event(FAKE_SLUG)
    await eventually(lambda: bool(handler.events))

    assert handler.events[0].slug == FAKE_SLUG

    await consumer.stop(0.2)

    mgs_in_queue = await count_messages(rabbitmq.queue)
    mgs_in_dlq = await count_messages(rabbitmq.dlq)

    assert mgs_in_queue == 0
    assert mgs_in_dlq == 0


@dataclass
class InvalidEvent:
    name: str
    data: bytes


VALID_VERSION = 1
INVALID_VERSION = 2

VALID_EVENT_TYPE = LINK_ACCESSED_EVENT_TYPE
INVALID_EVENT_TYPE = "fake-type"

NOT_JSON_DATA = b"not a json"

TEST_CASES = [
    InvalidEvent(
        name="not a json",
        data=NOT_JSON_DATA,
    ),
    InvalidEvent(
        name="invalid version",
        data=generate_link_accessed_event_json(
            version=INVALID_VERSION,
            event_type=VALID_EVENT_TYPE,
            slug=FAKE_SLUG,
        ).encode("utf-8"),
    ),
    InvalidEvent(
        name="invalid event type",
        data=generate_link_accessed_event_json(
            version=VALID_VERSION,
            event_type=INVALID_EVENT_TYPE,
            slug=FAKE_SLUG,
        ).encode("utf-8"),
    ),
]


@pytest.mark.parametrize(
    "case",
    TEST_CASES,
    ids=[case.name for case in TEST_CASES],
)
async def test_invalid_event_format_sent_to_dlq(case, rabbitmq):
    handler = FakeHandler()

    consumer = LinkAccessedConsumer(
        rabbitmq.queue,
        handler,
    )

    await consumer.start()
    await publish_raw(rabbitmq.exchange, case.data)
    await consumer.stop(0.2)

    assert len(handler.events) == 0

    mgs_in_dlq = await count_messages(rabbitmq.dlq)
    assert mgs_in_dlq == 1

    dlq_msg = await wait_message(rabbitmq.dlq)
    assert dlq_msg.body == case.data

    mgs_in_queue = await count_messages(rabbitmq.queue)
    assert mgs_in_queue == 0


async def test_message_sent_to_dlq_with_exception_while_handler_processing(rabbitmq):
    handler = FakeHandler()
    handler.set_error(RuntimeError("BOOM"))

    publisher = RabbitMQBroker(rabbitmq.exchange)
    consumer = LinkAccessedConsumer(
        rabbitmq.queue,
        handler,
    )

    await consumer.start()
    await publisher.publish_accessed_link_event(FAKE_SLUG)
    await consumer.stop(0.2)

    msg_in_queue = await count_messages(rabbitmq.queue)
    assert msg_in_queue == 0

    msg_in_dlq = await count_messages(rabbitmq.dlq)
    assert msg_in_dlq == 1

    msg = await wait_message(rabbitmq.dlq)
    assert json.loads(msg.body.decode("utf-8"))["slug"] == FAKE_SLUG


STOP_TIMEOUT = 0.5


async def test_stop_by_timeout_returns_message_to_queue(rabbitmq):
    channel = await rabbitmq.connection.channel()
    queue = await channel.get_queue(LAST_ACCESSED_QUEUE)

    handler = FakeHandler()
    handler.lock_execution()
    consumer = LinkAccessedConsumer(queue, handler)

    await consumer.start()
    try:
        await RabbitMQBroker(rabbitmq.exchange).publish_accessed_link_event(FAKE_SLUG)
        await eventually(lambda: handler.events)

        # Handler завис: stop() должен вернуться по таймауту, а не ждать вечно
        await asyncio.wait_for(consumer.stop(STOP_TIMEOUT), timeout=STOP_TIMEOUT + 2)

        await channel.close()

        assert await eventually(lambda: count_messages(rabbitmq.queue)) == 1
        assert await count_messages(rabbitmq.dlq) == 0

        msg = await wait_message(rabbitmq.queue)
        assert msg.redelivered
        assert LinkAccessedEvent.model_validate_json(msg.body).slug == FAKE_SLUG
    finally:
        handler.unlock_execution()
        await consumer.stop(STOP_TIMEOUT)
