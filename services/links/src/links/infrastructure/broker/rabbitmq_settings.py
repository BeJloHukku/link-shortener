import logging


import aio_pika
from aio_pika import ExchangeType, RobustConnection
from aio_pika.abc import (
    AbstractRobustExchange,
)

from links.settings import RABBITMQ_URL

logger = logging.getLogger(__name__)

LINKS_EXCHANGE = "links.events"


async def connect_rabbitmq() -> tuple[RobustConnection, AbstractRobustExchange] | None:
    try:
        connection = await aio_pika.connect_robust(
            url=RABBITMQ_URL,
            timeout=5,
        )
    except Exception:
        logger.exception("RabbitMQ connection failed. Server starting without broker")
        return None

    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            name=LINKS_EXCHANGE,
            type=ExchangeType.TOPIC,
            durable=True,
        )
    except Exception:
        logger.exception("Declaring exchange failed. Server starting without broker")
        return None

    return connection, exchange
