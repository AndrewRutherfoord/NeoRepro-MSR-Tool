from contextlib import asynccontextmanager
import json

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response

import logging

from pydantic import BaseModel

from backend.jobs_queue import DrillerClient, RabbitMQManager

logger = logging.getLogger(__name__)

router = APIRouter()

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


def apply_defaults(defaults : ProjectConfigDefaults, projects : list[ProjectConfig]) -> dict:
    results = []
    for i in range(len(projects)):
        results.append(defaults.__dict__ | projects[i].__dict__)
    return results

@router.post("/jobs")
async def create_job(
    jobs: JobConfigs,
    background_tasks: BackgroundTasks,
    request: Request
):
    projects : dict = apply_defaults(jobs.repositories.defaults, jobs.repositories.projects)
    for project in projects:
        # logger.warning(project)
        background_tasks.add_task(request.state.driller_client.call, json.dumps({"project": project, "neo": jobs.neo.__dict__ }))
    # result = await driller_client.call(body)
    return Response("body", status_code=200)