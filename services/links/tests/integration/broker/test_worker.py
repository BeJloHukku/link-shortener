import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import (
    UTC,
    datetime,
)
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from tests.integration.broker.helpers import (
    count_messages,
    eventually,
    publish_raw,
    wait_message,
)

from links.application.events import LinkAccessedEvent
from links.infrastructure.db.models import ShortUrl
from links.worker import run

pytestmark = [pytest.mark.docker, pytest.mark.integration]

SLUG = "worker-test"
BASE_TIME = datetime(2026, 1, 1, 12)
ACCESSED_AT = datetime(2026, 1, 2, 12, tzinfo=UTC)


@asynccontextmanager
async def running_worker(amqp_url, session_factory):
    stop = asyncio.Event()
    task = asyncio.create_task(run(stop, amqp_url=amqp_url, session_factory=session_factory))
    try:
        yield
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=25)


def make_event(slug=SLUG):
    return LinkAccessedEvent(
        event_id=uuid4(),
        event_type="link.accessed",
        version=1,
        slug=slug,
        occurred_at=ACCESSED_AT,
    )


async def test_worker_updates_last_accessed_at(rabbitmq, amqp_url, session, repository):
    await repository.add(
        slug=SLUG,
        origin_url="https://example.com",
        last_accessed_at=BASE_TIME,
    )
    session_factory = async_sessionmaker(session.bind, expire_on_commit=False)

    async def updated_link():
        async with session_factory() as read_session:
            link = await read_session.get(ShortUrl, SLUG)
            return link.last_accessed_at == ACCESSED_AT.replace(tzinfo=None)

    async with running_worker(amqp_url, session_factory):
        await publish_raw(rabbitmq.exchange, make_event().model_dump_json().encode())
        await eventually(updated_link)

    assert await count_messages(rabbitmq.queue) == 0
    assert await count_messages(rabbitmq.dlq) == 0


async def test_worker_sends_invalid_message_to_dlq(rabbitmq, amqp_url, session):
    session_factory = async_sessionmaker(session.bind, expire_on_commit=False)
    body = b"not a json"

    async with running_worker(amqp_url, session_factory):
        await publish_raw(rabbitmq.exchange, body)
        message = await wait_message(rabbitmq.dlq)
        assert message.body == body
        await message.ack()

    assert await count_messages(rabbitmq.queue) == 0
    assert await count_messages(rabbitmq.dlq) == 0


async def test_worker_accepts_unknown_slug(rabbitmq, amqp_url, session, caplog):
    session_factory = async_sessionmaker(session.bind, expire_on_commit=False)
    event = make_event(slug="unknown-slug")
    caplog.set_level(logging.INFO, logger="links.worker")

    async with running_worker(amqp_url, session_factory):
        await publish_raw(rabbitmq.exchange, event.model_dump_json().encode())
        # This log is emitted after the database operation completes successfully.
        await eventually(
            lambda: any(
                record.name == "links.worker"
                and record.getMessage()
                == f"Event {event.event_id} did not replace link {event.slug}"
                for record in caplog.records
            )
        )

    async with session_factory() as read_session:
        assert await read_session.get(ShortUrl, event.slug) is None
    assert await count_messages(rabbitmq.queue) == 0
    assert await count_messages(rabbitmq.dlq) == 0
