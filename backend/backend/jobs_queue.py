import asyncio, json, logging, os, queue, threading, time
from typing import MutableMapping
import uuid
from aio_pika import IncomingMessage, Message, connect, Channel, RobustConnection

from aio_pika import Message, connect
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractIncomingMessage,
    AbstractQueue,
)

import logging

from sqlmodel import Session
from backend.database import engine, get_session
from backend.ws_connection_manager import socket_connections
from common.models.jobs import Job, JobStatus, JobDetails

logger = logging.getLogger(__name__)


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
            logger.error(f"Bad message {message!r}")
            return

        logger.warning(message.body)
        response = json.loads(message.body)
        job_id = response.get("job_id")
        status = response.get("status")
        with Session(engine) as session:
            job_status = JobStatus(job_id=job_id, status=status)
            session.add(job_status)
            session.commit()
            session.refresh(job_status)

            job = session.get(Job, job_id)

        await socket_connections.send_message(
            {
                "job_status": job_status.model_dump(),
                "job": job.model_dump(),
            },
            ws_token="1",
        )

    async def call(self, body: str) -> str:
        correlation_id = str(uuid.uuid4())
        logger.debug(f"Sending message {correlation_id}: {body}")

        await self.channel.default_exchange.publish(
            Message(
                body.encode(),
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=self.queue,
        )

    async def close(self):
        self.channel.close()
        self.connection.close()
