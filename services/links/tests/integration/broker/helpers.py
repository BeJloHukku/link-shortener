import asyncio

from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractQueue,
)


async def eventually(
    predicate,
    timeout: int = 5,
    interval: float = 0.5,
) -> AbstractIncomingMessage:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while True:
        result = await predicate()
        if result:
            return result
        if loop.time() > deadline:
            raise AssertionError(f"Condition not get for {timeout}s")
        await asyncio.sleep(interval)


async def wait_message(
    queue: AbstractQueue,
    timeout: int = 5,
) -> AbstractIncomingMessage:
    return await eventually(
        predicate=lambda: queue.get(fail=False),
        timeout=timeout,
    )
