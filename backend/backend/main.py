from contextlib import asynccontextmanager
import os

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import logging

from sqlmodel import Session, select

from backend.database import create_db_and_tables, engine
from backend.jobs_queue import DrillerClient
from backend.routers import driller_router, queries

logger = logging.getLogger(__name__)

user = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
passwd = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")
host = os.environ.get("RABBITMQ_HOST", "127.0.0.1")
port = os.environ.get("RABBITMQ_PORT", 5672)

driller_client = None

# ---------- Rabbit MQ ----------


async def setup_jobs_queue():
    global driller_client
    driller_client = await DrillerClient().connect()


async def teardown_jobs_queue():
    global driller_client
    await driller_client.close()
    driller_client = None


async def get_client(request: Request) -> DrillerClient:
    global driller_client

    if driller_client is None or driller_client.connection.is_closed:
        driller_client = await DrillerClient().connect()
        logger.warning("Setting client")

    # Sets the drill client state in request. Can be accessed in endpoint with request injection and `request.state.driller_client`
    request.state.driller_client = driller_client
    return driller_client


# ---------- FastAPi ----------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup the queue on startup
    await setup_jobs_queue()

    yield

    # Disconnect the queue on teardown.
    await teardown_jobs_queue()


app = FastAPI(
    dependencies=[Depends(get_client)], lifespan=lifespan
)

app.include_router(driller_router.router)
app.include_router(queries.router, prefix="/queries")

origins = [
    "http://localhost:5173",
]

# Very open CORS. Stricter not necessary since app won't be deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def test():
    logger.warning("TEST")
    return Response("hello", status_code=200)
