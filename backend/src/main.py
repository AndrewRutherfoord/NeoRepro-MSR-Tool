from contextlib import asynccontextmanager
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import logging


from src.drill_queue_rpc import RabbitMessageQueueRPC, RepositoryDrillerClient
from src.routers import driller_router, files, job_statuses

logger = logging.getLogger(__name__)

user = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
passwd = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")
host = os.environ.get("RABBITMQ_HOST", "127.0.0.1")
port = os.environ.get("RABBITMQ_PORT", 5672)

driller_client: RabbitMessageQueueRPC | None = None

# ---------- Rabbit MQ ----------


async def setup_jobs_queue():
    global driller_client
    driller_client = RepositoryDrillerClient(user, passwd, host, port)
    await driller_client.connect()


async def teardown_jobs_queue():
    global driller_client
    if driller_client is not None:
        await driller_client.close()
    driller_client = None


async def get_client(request: Request = None) -> RabbitMessageQueueRPC:
    """Gets the RabbitMQ Driller RPC Client
    To be used with dependency ejection for endpoint to access the RPC client.
    """
    global driller_client

    if driller_client is None or driller_client.connection.is_closed:
        raise ConnectionError("Could not connect to RabbitMQ client.")

    if request is not None:
        # Sets the drill client state in request. Can be accessed in endpoint with request injection and `request.state.driller_client`
        request.state.driller_client = driller_client
        return driller_client
    return None


# ---------- FastAPi ----------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup the RPC Queue on startup
    await setup_jobs_queue()

    yield

    # Disconnect the queue on teardown.
    await teardown_jobs_queue()

# Instantiate app with global dependency injection and the lifespan
# `get_client` adds the Rabbit MQ RPC instance to the request object
app = FastAPI(dependencies=[Depends(get_client)], lifespan=lifespan)

# Attach the routers to the FastAPI App
app.include_router(driller_router.router)
app.include_router(files.router)
app.include_router(job_statuses.router)

# Allow the Vue JS frontend to access the backend. 
# Default port is 5173 but can be set in environment file.
origins = [
    f"http://localhost:{os.environ.get('FRONTEND_PORT', 5173)}",
    f"http://127.0.0.1:{os.environ.get('FRONTEND_PORT', 5173)}"
]

# Very open CORS. Stricter not necessary since app won't be deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthcheck")
def get_healthcheck():
    """Endpoint to use to check backend life."""
    return "OK"
