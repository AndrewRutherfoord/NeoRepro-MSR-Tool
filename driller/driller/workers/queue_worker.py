import logging
from abc import ABC, abstractmethod

import pika

logger = logging.getLogger(__name__)

class QueueWorker(ABC):

    def __init__(self, host, port, queue):
        self.host = host
        self.port = port
        self.queue = queue

        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port)
            )
            self.channel = self.connection.channel()
        except:
            logger.exception("Could not connect to message queue.")

    @abstractmethod
    def on_request(ch, method, props, body):
        pass

    def consume_jobs(self):
        self.channel.queue_declare(queue=self.queue)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.on_request)

        logger.info(f"Awaiting Tasks on queue '{self.queue}'.")
        self.channel.start_consuming()

    def close(self):
        self.connection.close()
