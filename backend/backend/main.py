from contextlib import asynccontextmanager
import os
from typing import Union

from aio_pika import Channel, IncomingMessage, Message
from fastapi import Depends, FastAPI, Response

import logging

from pydantic import BaseModel

from backend.jobs_queue import RabbitMQManager

logger = logging.getLogger(__name__)

user = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
passwd = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")
host = os.environ.get("RABBITMQ_HOST", "127.0.0.1")
port = os.environ.get("RABBITMQ_PORT", 5672)

rabbitmq_manager = RabbitMQManager(
    f"amqp://{user}:{passwd}@{host}:{port}/",
    queue_name="fastapi",
    callback_queue_name="logs",
)


async def process_message(message: IncomingMessage):
    async with message.process():
        print("Received message:", message.body.decode())


async def setup_jobs_queue():
    await rabbitmq_manager.get_channel()
    await rabbitmq_manager.consume(process_message)


async def teardown_jobs_queue():
    await rabbitmq_manager._channel.close()
    await rabbitmq_manager._connection.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    logger.info("Startup lifespan hook.")
    await setup_jobs_queue()

    yield

    logger.info("Shutdown lifespan hook.")
    await teardown_jobs_queue()


app = FastAPI()


@app.get("/")
async def test():
    return Response("hello", status_code=200)


class Job(BaseModel):
    neo: dict
    project: dict


@app.post("/jobs")
async def create_job(
    job: Job, channel: Channel = Depends(rabbitmq_manager.get_channel)
):
    print(job.project)
    print(job.neo)
    body = str(job.model_dump())
    await channel.default_exchange.publish(Message(body=body.encode()), routing_key="fastapi", callback_queue_name="logs")
    return Response("", status_code=204)
