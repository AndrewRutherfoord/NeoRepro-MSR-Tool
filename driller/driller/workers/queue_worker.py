import asyncio
import logging
from abc import ABC, abstractmethod

import aio_pika

logger = logging.getLogger(__name__)


class Worker(ABC):
    """Abstract definition of a worker class which will wait for jobs and complete them until `close()` is called"""

    async def start(self):
        """Starts the worker."""
        pass

    async def close(self):
        """Stops worker waiting for jobs"""
        pass


class QueueWorker(Worker):

    def __init__(self, host, port, user, password, queue_name, heartbeat_interval=30):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.queue_name = queue_name

        self.connection = None
        self.channel = None

        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_task = None

    async def connect(self):

        try:
            # Perform connection
            self.connection = await aio_pika.connect(
                f"amqp://{self.password}:{self.user}@{self.host}:{self.port}/"
            )

            # Creating a channel
            self.channel = await self.connection.channel()

            # Setting prefetch count to 1 ensures that work is distrubuted evenly.
            await self.channel.set_qos(prefetch_count=1)
            self.exchange = self.channel.default_exchange

            # Declaring queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
            )
            logger.info("Connected to amqp...")
        except Exception as e:
            logger.exception("Could not connect to message queue.", e)

    @abstractmethod
    def on_request(
        self,
        body: str,
        message: aio_pika.abc.AbstractIncomingMessage,
    ) -> str:
        """
        Processes a queue item when received from the exchange.

        Args:
            body (str): Body of the queue item.
        Returns:
            str: JSON response string.
        """
        pass

    async def send_response(
        self, message: aio_pika.abc.AbstractIncomingMessage, response: str
    ):
        if message.reply_to is None:
            raise ValueError("Message must contain a `reply_to` field.")
        logger.info(f"Sending response: {response}")
        await self.exchange.publish(
            aio_pika.Message(
                body=response.encode(),
                correlation_id=message.correlation_id,
            ),
            routing_key=message.reply_to,
        )

    async def on_before_start_job(
        self, job_body, message: aio_pika.abc.AbstractIncomingMessage
    ):
        logger.debug(f"Job started: {job_body}")

    async def on_after_finish_job(
        self, job_response: str, message: aio_pika.abc.AbstractIncomingMessage
    ):
        if message.reply_to is None:
            raise ValueError("Message must contain a `reply_to` field.")
        logger.debug("Request complete")

        await self.exchange.publish(
            aio_pika.Message(
                body=job_response.encode(),
                correlation_id=message.correlation_id,
            ),
            routing_key=message.reply_to,
        )

    async def on_job_failed(
        self, exception, message: aio_pika.abc.AbstractIncomingMessage
    ):
        logger.exception("Job failed: %s", exception)

    async def consume_jobs(self):
        try:
            async with self.queue.iterator() as qiterator:
                message: aio_pika.abc.AbstractIncomingMessage
                async for message in qiterator:
                    try:
                        async with message.process(requeue=False):
                            assert message.reply_to is not None

                            body = message.body.decode()

                            await self.handle_request(body, message)
                    except Exception as e:
                        await self.on_job_failed(e, message)
        except aio_pika.exceptions.ChannelInvalidStateError:
            # Thrown on graceful exit.
            return

    async def handle_request(self, body, message):
        loop = asyncio.get_event_loop()

        await self.on_before_start_job(body, message)

        response = await loop.run_in_executor(None, self.on_request, body, message)

        await self.on_after_finish_job(response, message)

        return response

    async def send_heartbeat(self):
        try:
            while self.connection is not None:
                await self.connection.ready()
                logger.debug("Heartbeat sent")

            await asyncio.sleep(self.heartbeat_interval)

        except Exception as e:
            logger.exception("Heartbeat failed: %s", e)

    async def heartbeat(self):
        await asyncio.sleep(self.heartbeat_interval)
        while self.channel is not None:
            await self.channel.heartbeat_tick()
            await asyncio.sleep(self.heartbeat_interval)

    async def start(self):
        await self.connect()
        self.heartbeat_task = asyncio.create_task(self.heartbeat())
        await self.consume_jobs()

    async def close(self):
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
