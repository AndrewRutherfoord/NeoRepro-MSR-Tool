import asyncio
from dataclasses import asdict
import json
import logging
import time
from typing import MutableMapping
import pika
import uuid

# from driller.config_driller import DrillConfig, apply_defaults
from driller.settings.default import LOG_FORMAT, LOG_LEVEL
from driller.util import load_yaml, parse_config
from .driller_config import DrillConfig, apply_defaults

from aio_pika import Message, connect
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)

logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)
pika_logger = logging.getLogger("pika")
pika_logger.setLevel(logging.WARNING)

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

    async def call(self, task: DrillConfig) -> str:
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        self.futures[correlation_id] = future

        await self.channel.default_exchange.publish(
            Message(
                task.to_json().encode(),
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=self.queue,
        )

        return await future

#     def __init__(self):
#         self.connection = pika.BlockingConnection(
#             pika.ConnectionParameters(host="localhost")
#         )

#         self.channel = self.connection.channel()

#         result = self.channel.queue_declare(queue="", exclusive=True)
#         self.callback_queue = result.method.queue

#         self.channel.basic_consume(
#             queue=self.callback_queue,
#             on_message_callback=self.on_response,
#             auto_ack=True,
#         )

#         self.response = None
#         self.corr_id = None

#     def on_response(self, ch, method, props, body):
#         if self.corr_id == props.correlation_id:
#             self.response = body

#     def call(self, task: DrillConfig):
#         task.neo = None
#         self.response = None
#         self.corr_id = str(uuid.uuid4())
#         self.channel.basic_publish(
#             exchange="",
#             routing_key="driller_queue",
#             properties=pika.BasicProperties(
#                 reply_to=self.callback_queue,
#                 correlation_id=self.corr_id,
#             ),
#             body=task.to_json(),
#         )
#         while self.response is None:
#             self.connection.process_data_events(time_limit=None)
#         return self.response

def get_drill_configs(file) -> list[DrillConfig]:
    conf = load_yaml(file)
    neo, defaults, projects = parse_config(conf)
    
    configs = []
    for project in projects:
        p = apply_defaults(project, defaults=defaults)
        configs.append(DrillConfig(neo=neo, project=p))
    
    return configs

async def main():
    driller = await DrillerClient().connect()
    configs = get_drill_configs("driller/configs/test.yaml")

    for conf in configs:
        response = await  driller.call(conf)
        logger.info(response)

def exec():
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())