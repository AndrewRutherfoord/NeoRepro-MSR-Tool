import asyncio
import logging
from abc import ABC, abstractmethod

import aio_pika

logger = logging.getLogger(__name__)


class QueueWorker(ABC):

    def __init__(self, host, port, queue_name):
        self.host = host
        self.port = port
        self.queue_name = queue_name

        self.connection = None
        self.channel = None

    async def connect(self):
        try:
            # Perform connection
            self.connection = await aio_pika.connect(
                f"amqp://guest:guest@{self.host}:{self.port}/"
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
        except:
            logger.exception("Could not connect to message queue.")

    @abstractmethod
    def on_request(
        self,
        body: str,
    ) -> str:
        """
        Processes a queue item when received from the exchange.

        Args:
            body (str): Body of the queue item.
        Returns:
            str: JSON response string.
        """
        pass

    async def consume_jobs(self):
        async with self.queue.iterator() as qiterator:
            message: aio_pika.abc.AbstractIncomingMessage
            async for message in qiterator:
                try:
                    async with message.process(requeue=False):
                        assert message.reply_to is not None

                        body = message.body.decode()
                        logger.info(f"Message received: {body}.")

                        response = self.on_request(body)

                        await self.exchange.publish(
                            aio_pika.Message(
                                body=response.encode(),
                                correlation_id=message.correlation_id,
                            ),
                            routing_key=message.reply_to,
                        )
                        logger.info("Request complete")
                except Exception:
                    logging.exception("Processing error for message %r", message)
        # self.channel.queue_declare(queue=self.queue)

        # self.channel.basic_qos(prefetch_count=1)
        # self.channel.basic_consume(queue=self.queue, on_message_callback=self.on_request)

        # logger.info(f"Awaiting Tasks on queue '{self.queue}'.")
        # self.channel.start_consuming()

    def close(self):
        self.channel.close()
        self.connection.close()
