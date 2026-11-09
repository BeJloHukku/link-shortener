import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import AsyncIterator

from aio_pika import connect_robust
from aio_pika.abc import (
    AbstractChannel,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from links.application.events import LinkAccessedEvent
from links.application.use_cases import RecordLinkAccessUseCase
from links.infrastructure.broker.consumer import LinkAccessedConsumer
from links.infrastructure.broker.rabbitmq_settings import declare_topology
from links.infrastructure.db.db import engine, new_session
from links.infrastructure.db.repository import SqlAlchemyLinkRepository
from links.settings import RABBITMQ_URL
from links.infrastructure.broker.consumer import Handler

CONNECTION_RABBITMQ_TIMEOUT = 5.0
PREFETCH_COUNT = 20
STOP_TIMEOUT = 20.0

logger = logging.getLogger("links.worker")


def make_handler(session_factory: async_sessionmaker[AsyncSession]) -> Handler:
    async def handler(event: LinkAccessedEvent) -> None:
        async with session_factory() as session:
            db = SqlAlchemyLinkRepository(session)
            use_case = RecordLinkAccessUseCase(db)
            is_replaced = await use_case.execute(
                slug=event.slug,
                accessed_at=event.occurred_at,
            )
            if not is_replaced:
                logger.info("Event %s did not replace link %s", event.event_id, event.slug)

    return handler


@asynccontextmanager
async def connect_rabbitmq(url: str) -> AsyncIterator[AbstractChannel]:
    connection = await connect_robust(
        url=url,
        timeout=CONNECTION_RABBITMQ_TIMEOUT,
    )

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=PREFETCH_COUNT)
        yield channel


async def run(
    stop: asyncio.Event,
    *,
    amqp_url: str,
    session_factory: async_sessionmaker[AsyncSession],
):
    async with connect_rabbitmq(amqp_url) as channel:
        _, queue = await declare_topology(channel)
        consumer = LinkAccessedConsumer(
            queue=queue,
            handler=make_handler(session_factory),
        )
        await consumer.start()
        try:
            await stop.wait()
        finally:
            await consumer.stop(timeout=STOP_TIMEOUT)


def install_signal_handler(stop: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            stop.set,
        )


async def _main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    stop = asyncio.Event()
    install_signal_handler(stop)
    try:
        logging.info("Worker is starting...")
        await run(
            stop=stop,
            amqp_url=RABBITMQ_URL,
            session_factory=new_session,
        )
    finally:
        await engine.dispose()
        logging.info("Worker is stopped")


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()
