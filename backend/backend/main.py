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

class ProjectConfigDefaults(BaseModel):
    start_date : str
    end_date : str
    index_code : bool
    index_developer_email : bool
    
class ProjectConfig(BaseModel):
    project_id : str
    repo : str
    url : str = None

    start_date : str = None
    end_date : str = None
    index_code : bool = False
    index_developer_email : bool = False

class RepositoriesConfig(BaseModel):
    defaults: ProjectConfigDefaults
    projects: list[ProjectConfig]

class NeoConfig(BaseModel):
    db_url : str
    port : int
    db_user : str
    db_pwd : str
    batch_size : int

class JobConfigs(BaseModel):
    neo: NeoConfig = None  # optional. Can be filled from env vars in worker.
    repositories: RepositoriesConfig


async def get_client() -> DrillerClient:
    global driller_client
    if driller_client is None or driller_client.connection.is_closed:
        driller_client = await DrillerClient().connect()
    return driller_client

def apply_defaults(defaults : ProjectConfigDefaults, projects : list[ProjectConfig]) -> dict:
    results = []
    for i in range(len(projects)):
        results.append(defaults.__dict__ | projects[i].__dict__)
    return results

@app.post("/jobs")
async def create_job(
    jobs: JobConfigs,
    background_tasks: BackgroundTasks,
    driller_client: DrillerClient = Depends(get_client),
):
    projects : dict = apply_defaults(jobs.repositories.defaults, jobs.repositories.projects)
    for project in projects:
        # logger.warning(project)
        background_tasks.add_task(driller_client.call, json.dumps({"project": project, "neo": jobs.neo.__dict__ }))
    # result = await driller_client.call(body)
    return Response("body", status_code=200)
