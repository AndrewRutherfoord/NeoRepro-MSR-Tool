from contextlib import asynccontextmanager
import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response

import logging

from pydantic import BaseModel
from sqlmodel import Session, select

from backend.jobs_queue import DrillerClient, RabbitMQManager
from backend.database import engine
from backend.models.jobs import Job, JobDetails

logger = logging.getLogger(__name__)

router = APIRouter()


class ProjectConfigDefaults(BaseModel):
    start_date: str
    end_date: str
    index_code: bool
    index_developer_email: bool


class ProjectConfig(BaseModel):
    project_id: str
    repo: str
    url: str = None

    start_date: str = None
    end_date: str = None
    index_code: bool = False
    index_developer_email: bool = False


class RepositoriesConfig(BaseModel):
    defaults: ProjectConfigDefaults
    projects: list[ProjectConfig]


class NeoConfig(BaseModel):
    db_url: str
    port: int
    db_user: str
    db_pwd: str
    batch_size: int


class JobConfigs(BaseModel):
    neo: NeoConfig = None  # optional. Can be filled from env vars in worker.
    repositories: RepositoriesConfig


def apply_defaults(
    defaults: ProjectConfigDefaults, projects: list[ProjectConfig]
) -> dict:
    results = []
    for i in range(len(projects)):
        results.append(defaults.__dict__ | projects[i].__dict__)
    return results


@router.get("/jobs/")
def list_jobs(offset: int = 0, limit: int = Query(default=100, le=100)):
    with Session(engine) as session:
        jobs = session.exec(select(Job).offset(offset).limit(limit)).all()
        return jobs
    
@router.get("/jobs/{job_id}", response_model=JobDetails)
def detail_job(job_id: int):
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
        
@router.post("/test-jobs/")
def create_hero(hero: Job):
    with Session(engine) as session:
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return hero

@router.post("/jobs")
async def create_job(
    jobs: JobConfigs, background_tasks: BackgroundTasks, request: Request
):
    projects: dict = apply_defaults(
        jobs.repositories.defaults, jobs.repositories.projects
    )
    for project in projects:
        # logger.warning(project)
        background_tasks.add_task(
            request.state.driller_client.call,
            json.dumps(
                {
                    "project": project,
                    "neo": jobs.neo.__dict__ if jobs.neo is not None else None,
                }
            ),
        )
    # result = await driller_client.call(body)
    return Response("body", status_code=200)
