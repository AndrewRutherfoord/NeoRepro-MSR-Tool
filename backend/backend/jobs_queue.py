import asyncio, json, logging, os, queue, threading, time
from typing import MutableMapping
import uuid
from aio_pika import IncomingMessage, Message, connect, Channel, RobustConnection

from aio_pika import Message, connect
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)

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

class DrillerClient(object):
    queue = "driller_queue"
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue
    
    def __init__(self) -> None:
        self.futures: MutableMapping[str, asyncio.Future] = {}
    
    async def connect(self) -> "DrillerClient":
        self.connection = await connect("amqp://guest:guest@localhost:5672/")
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self.on_response, no_ack=True)

        return self

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            print(f"Bad message {message!r}")
            return

        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

    async def call(self, body : str) -> str:
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        self.futures[correlation_id] = future

        await self.channel.default_exchange.publish(
            Message(
                body.encode(),
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=self.queue,
        )

        return await future
    
    async def close(self):
        self.channel.close()
        self.connection.close()
        
