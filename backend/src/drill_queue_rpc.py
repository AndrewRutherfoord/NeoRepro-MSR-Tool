import asyncio, json, logging
from typing import MutableMapping
from abc import ABC, abstractmethod
import uuid
from aio_pika import IncomingMessage, Message, connect, Channel, RobustConnection

from aio_pika import Message, connect
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractIncomingMessage,
    AbstractQueue,
)

from sqlmodel import Session
from src.database import engine
from src.ws_connection_manager import socket_connections
from common.models.jobs import Job, JobStatus

logger = logging.getLogger(__name__)


class RabbitMessageQueueRPC(ABC):
    """This is an implementation of a remote procedure call based on
    https://aio-pika.readthedocs.io/en/latest/rabbitmq-tutorial/6-rpc.html
    Calls a function on a remote worker that executes a job.
    Waits for callback messages. And executes `process_response` on the message.
    `process_response` shoud be overridden with handling of message.
    """

    connection: AbstractConnection
    channel: AbstractChannel
    call_queue = "driller_queue"
    callback_queue: AbstractQueue

    def __init__(self, user, password, host, port):
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    async def connect(self) -> "RabbitMessageQueueRPC":
        connection_string = (
            f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"
        )
        self.connection = await connect(connection_string)
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)

        await self.callback_queue.consume(self.on_response, no_ack=True)

        return self

    @abstractmethod
    async def process_response(self, response: dict) -> None:
        pass

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            logger.error(f"Bad message {message!r}")
            return

        logger.warning(message.body)
        response = json.loads(message.body)

        await self.process_response(response)

    async def call(self, body: str):
        correlation_id = str(uuid.uuid4())
        logger.debug(f"Sending message {correlation_id}: {body}")

        await self.channel.default_exchange.publish(
            Message(
                body.encode(),
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=self.call_queue,
        )

    async def close(self):
        await self.channel.close()
        await self.connection.close()


class RepositoryDrillerClient(RabbitMessageQueueRPC):
    """Implementation of the RPC with Rabbit MQ.
    Calling this creates a drill job on a message queue which is then executed by the driller-worker
    docker container.
    Once when drill jobs are started and when they are finished they send responses. This client
    processes these reponses and creates the associates JobStatuses in the database.
    """

    queue = "driller_queue"
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue

    async def process_response(self, response: dict) -> None:
        try:
            job_id = response.get("job_id")
            status = response.get("status")
            message = response.get("message", "")
        except KeyError as e:
            logger.error(f"Queue Response is missing key {e}")
            return

        with Session(engine) as session:
            job_status = JobStatus(job_id=job_id, status=status, message=message)
            session.add(job_status)
            session.commit()
            session.refresh(job_status)

            job = session.get(Job, job_id)
        logger.debug("Sending socket message")
        await socket_connections.send_message(
            {
                "job_status": job_status.model_dump(),
                "job": job.model_dump(),
            },
        )
