import asyncio, json, logging, os, queue, threading, time
from aio_pika import IncomingMessage, Message, connect, Channel, RobustConnection


class RabbitMQManager:
    def __init__(self, url: str, queue_name="fastapi", callback_queue_name="logs"):
        self._url = url
        self._connection: RobustConnection = None
        self._channel: Channel = None
        self.queue_name = queue_name
        self._queue = None
        self.callback_queue_name = callback_queue_name
        self._callback_queue = None

    async def get_channel(self) -> Channel:
        if not self._connection:
            self._connection = await connect(self._url)

        if not self._channel or self._channel.is_closed:
            self._channel = await self._connection.channel()

        if not self._queue:
            self._queue = await self._channel.declare_queue(self.queue_name)

        return self._channel

    async def consume(self, callback):
        channel = await self.get_channel()
        # Make sure the queue exists
        self._callback_queue = await channel.declare_queue(
            self.callback_queue_name, durable=True
        )
        # Start consuming messages
        return await self._callback_queue.consume(callback)
