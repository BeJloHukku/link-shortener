import logging

import aio_pika
from aio_pika import (
    ExchangeType,
    RobustConnection,
)
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractQueue,
)

logger = logging.getLogger(__name__)

LINKS_EXCHANGE = "links.events"
LAST_ACCESSED_QUEUE = "links.last_accessed"
LAST_ACCESSED_DLQ = "links.last_accessed.dlq"
LINK_ACCESSED_ROUTING_KEY = "link.accessed"


async def declare_topology(
    channel: AbstractChannel,
) -> tuple[AbstractExchange, AbstractQueue]:
    exchange = await channel.declare_exchange(
        name=LINKS_EXCHANGE,
        type=ExchangeType.TOPIC,
        durable=True,
    )

    await channel.declare_queue(
        name=LAST_ACCESSED_DLQ,
        durable=True,
    )

    queue = await channel.declare_queue(
        name=LAST_ACCESSED_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": LAST_ACCESSED_DLQ,
        },
    )

    await queue.bind(
        exchange=exchange,
        routing_key=LINK_ACCESSED_ROUTING_KEY,
    )

    return exchange, queue


async def connect_rabbitmq(url: str) -> tuple[RobustConnection, AbstractExchange] | None:
    try:
        connection = await aio_pika.connect_robust(
            url=url,
            timeout=5,
        )
    except Exception:
        logger.exception("RabbitMQ connection failed. Server starting without broker")
        return None

    try:
        channel = await connection.channel()
        exchange, _ = await declare_topology(channel)
    except Exception:
        logger.exception("Declaring topology failed. Server starting without broker")
        return None

    return connection, exchange
