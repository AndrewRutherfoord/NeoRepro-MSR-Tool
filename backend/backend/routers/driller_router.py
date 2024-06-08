from contextlib import asynccontextmanager
import json

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
)

import logging

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select, delete

from backend.jobs_queue import DrillerClient, RabbitMQManager
from backend.database import engine, get_session
from backend.models.jobs import (
    Job,
    JobBase,
    JobCreate,
    JobDetails,
    JobList,
    JobStatus,
    JobStatusDetails,
)

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


def get_job_status(session: Session, job_id: int):
    statement = (
        select(Job, JobStatus)
        .join(JobStatus, Job.id == JobStatus.job_id)
        .where(Job.id == job_id)
        .order_by(JobStatus.timestamp.desc())
    )
    result = session.execute(statement).first()
    return result if result else (None, None)


@router.get("/jobs/")
def list_jobs(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    result = session.exec(
        select(Job, JobStatus)
        .join(JobStatus, Job.id == JobStatus.job_id)
        # .where(Job.id == job_id)
        .order_by(JobStatus.timestamp.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    logger.warning(result)
    items = []
    for item in result:
        job, latest_status = item if item else (None, None)
        if job is None:
            return JSONResponse(status_code=404, content={"error": "Job not found"})
        items.append(JobList(id=job.id, name=job.name, data=job.data, status=latest_status.status))
    # job = result[0]
    # latest_status = result[1]

    return items


@router.delete("/jobs/{job_id}")
def delete_job(*, session: Session = Depends(get_session), job_id: int):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    session.delete(job)
    session.commit()
    return Response(status_code=200)

@router.delete("/jobs/")
def delete_all_jobs(*, session: Session = Depends(get_session)):
    results = session.exec(select(Job))
    for job in results:
        session.delete(job)
    session.commit()
    return Response(status_code=200)


@router.get("/jobs/{job_id}", response_model=JobDetails)
def detail_job(*, session: Session = Depends(get_session), job_id: int):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/test-jobs/")
def create_hero(*, session: Session = Depends(get_session), job: Job):
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.post("/jobs/status/")
def create_job_status(
    *, session: Session = Depends(get_session), job_status: JobStatus
):
    session.add(job_status)
    session.commit()
    session.refresh(job_status)
    return job_status


@router.get("/jobs/status/{job_status_id}", response_model=JobStatusDetails)
def detail_job_status(*, session: Session = Depends(get_session), job_status_id: int):
    job_status = session.get(JobStatus, job_status_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status


@router.post("/jobs/")
async def create_job(
    *,
    session: Session = Depends(get_session),
    jobs: JobConfigs,
    background_tasks: BackgroundTasks,
    request: Request
):
    projects: dict = apply_defaults(
        jobs.repositories.defaults, jobs.repositories.projects
    )
    jobs_list = []
    for project in projects:
        logger.warning(project)
        job_dict = {
            "project": project,
            "neo": jobs.neo.__dict__ if jobs.neo is not None else None,
        }

        db_job = Job.model_validate(JobCreate(name=project["project_id"], data=job_dict))

        session.add(db_job)
        session.commit()
        session.refresh(db_job)
        jobs_list.append(db_job)

        db_job_status = JobStatus(job_id=db_job.id)
        session.add(db_job_status)
        session.commit()
        session.refresh(db_job_status)
        # background_tasks.add_task(
        #     request.state.driller_client.call,
        #     json.dumps(
        #         {
        #             "project": project,
        #             "neo": jobs.neo.__dict__ if jobs.neo is not None else None,
        #         }
        #     ),
        # )
    # result = await driller_client.call(body)
    return Response("", status_code=201)
