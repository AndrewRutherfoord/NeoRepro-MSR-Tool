from contextlib import asynccontextmanager
import json
import os
from typing import Annotated, Union

from aio_pika import Channel, IncomingMessage, Message
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response

import logging

from pydantic import BaseModel

from backend.jobs_queue import DrillerClient, RabbitMQManager

logger = logging.getLogger(__name__)

user = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
passwd = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")
host = os.environ.get("RABBITMQ_HOST", "127.0.0.1")
port = os.environ.get("RABBITMQ_PORT", 5672)

driller_client = None

async def setup_jobs_queue():
    global driller_client
    driller_client = await DrillerClient().connect()


async def teardown_jobs_queue():
    global driller_client
    driller_client.close()
    driller_client = None

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    logger.info("Startup lifespan hook.")
    await setup_jobs_queue()

    yield

    logger.info("Shutdown lifespan hook.")
    await teardown_jobs_queue()



@app.get("/")
async def test():
    return Response("hello", status_code=200)


class Job(BaseModel):
    neo: dict = None
    project: dict

async def get_client() -> DrillerClient:
    global driller_client
    if driller_client is None or driller_client.connection.is_closed:
        driller_client = await DrillerClient().connect()
    return driller_client

@app.post("/jobs")
async def create_job(job: Job, background_tasks: BackgroundTasks,driller_client: DrillerClient = Depends(get_client)):
    body = json.dumps(job.model_dump())
    logger.info(body)
    background_tasks.add_task(driller_client.call, body)
    # result = await driller_client.call(body)
    return Response("", status_code=204)
