from contextlib import asynccontextmanager
import json
import os
from typing import Annotated, Union

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from aio_pika import Channel, IncomingMessage, Message
import logging

from pydantic import BaseModel

from backend.jobs_queue import DrillerClient, RabbitMQManager
from backend.routers import driller_router
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

async def get_client(request: Request) -> DrillerClient:
    global driller_client
    if driller_client is None or driller_client.connection.is_closed:
        driller_client = await DrillerClient().connect()
        logger.warning("Setting client")
    request.state.driller_client = driller_client
    return driller_client

app = FastAPI(dependencies=[Depends(get_client)])
app.include_router(driller_router.router)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

