import asyncio
import logging
from asyncio import Event
from typing import (
    Awaitable,
    Callable,
)

from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractQueue,
    ConsumerTag,
)
from pydantic import ValidationError

from links.application.events import LinkAccessedEvent

logger = logging.getLogger(__name__)

Handler = Callable[[LinkAccessedEvent], Awaitable[None]]


class LinkAccessedConsumer:
    def __init__(
        self,
        queue: AbstractQueue,
        handler: Handler,
    ):
        self._queue = queue
        self._handler = handler
        self._tag: ConsumerTag | None = None
        self._in_flight = 0
        self._idle = Event()
        self._idle.set()

    async def start(self) -> None:
        self._tag = await self._queue.consume(self._on_message)

    async def stop(self, timeout: float) -> None:
        if self._tag is not None:
            await self._queue.cancel(self._tag)
            self._tag = None

        try:
            await asyncio.wait_for(self._idle.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout of {self._in_flight} messages, returning to queue")

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        try:
            self._in_flight += 1
            self._idle.clear()
            await self._handle(message)
        finally:
            self._in_flight -= 1
            if self._in_flight == 0:
                self._idle.set()

    async def _handle(self, message: AbstractIncomingMessage) -> None:
        try:
            event = LinkAccessedEvent.model_validate_json(message.body)
        except ValidationError:
            logger.warning(
                f"Invalid message from {self._queue.name}: message_id={message.message_id}. Sent to DLQ"
            )
            await message.reject(requeue=False)
            return

        try:
            async with message.process():
                await self._handler(event)
        except Exception:
            logger.exception(
                f"Exception while processing message_id: {event.event_id}. Sent to DLQ"
            )
