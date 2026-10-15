from typing import AsyncGenerator

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractRobustConnection,
)

from links.settings import RABBITMQ_URL

rabbitmq_connection: AbstractRobustConnection | None = None


async def _get_rabbitmq_connection() -> AbstractRobustConnection:
    global rabbitmq_connection
    if rabbitmq_connection is None or rabbitmq_connection.is_closed:
        rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)

    assert rabbitmq_connection is not None
    return rabbitmq_connection


async def get_rabbitmq_channel() -> AsyncGenerator[AbstractChannel, None]:
    """Генератор, который выдает изолированный канал и автоматически его закрывает."""
    connection = await _get_rabbitmq_connection()
    async with connection.channel() as channel:
        yield channel
