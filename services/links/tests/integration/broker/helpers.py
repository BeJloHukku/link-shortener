import asyncio
import inspect
import json
import uuid
from typing import (
    Awaitable,
    Callable,
    overload,
)

from aio_pika import Message
from aio_pika.abc import (
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
)

from links.infrastructure.broker.rabbitmq_settings import LINK_ACCESSED_ROUTING_KEY


@overload
async def eventually[T](
    predicate: Callable[[], Awaitable[T | None]],
    timeout: float = 5,
    interval: float = 0.1,
) -> T: ...


@overload
async def eventually[T](
    predicate: Callable[[], T | None],
    timeout: float = 5,
    interval: float = 0.1,
) -> T: ...


async def eventually[T](
    predicate: Callable[[], T | Awaitable[T]],
    timeout: float = 5,
    interval: float = 0.1,
) -> T:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while True:
        result = predicate()
        if inspect.isawaitable(result):
            result = await result
        if result:
            return result
        if loop.time() > deadline:
            raise AssertionError(f"Condition not get for {timeout}s")
        await asyncio.sleep(interval)


async def wait_message(
    queue: AbstractQueue,
    timeout: float = 5,
) -> AbstractIncomingMessage:
    return await eventually(
        predicate=lambda: queue.get(fail=False),
        timeout=timeout,
    )


async def publish_raw(
    exchange: AbstractExchange,
    body: bytes,
) -> None:
    await exchange.publish(
        message=Message(body=body),
        routing_key=LINK_ACCESSED_ROUTING_KEY,
    )


async def count_messages(queue: AbstractQueue) -> int:
    mgs = await queue.declare()
    assert mgs.message_count is not None
    return mgs.message_count


def generate_link_accessed_event_json(
    version: int,
    event_type: str,
    slug: str,
) -> str:
    return json.dumps(
        {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "version": version,
            "slug": slug,
        }
    )
