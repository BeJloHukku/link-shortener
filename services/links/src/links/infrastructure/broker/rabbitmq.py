from aio_pika.abc import AbstractRobustChannel


class RabbitMQBroker:
    def __init__(self, channel: AbstractRobustChannel):
        pass

    async def publish_accessed_link_event(self, slug: str) -> None:
        pass
