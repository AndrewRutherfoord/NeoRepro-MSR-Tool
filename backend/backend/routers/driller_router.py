from contextlib import asynccontextmanager
from enum import Enum
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


class PydrillerConfig(BaseModel):
    since: str = None
    from_commit: str = None
    from_tag: str = None
    to: str = None
    to_commit: str = None
    to_tag: str = None
    only_in_branch: str = None
    only_no_merge: bool = False
    only_authors: list[str] = None
    only_commits: list[str] = None
    only_release: bool = False
    filepath: str = None
    only_modifications_with_file_types: list[str] = None


class FilterMethod(str, Enum):
    exact = "exact"
    not_exact = "!exact"
    contains = "contains"
    not_contains = "!contains"


# class CustomJSONEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Enum):
#             return obj.value
#         return super().default(obj)


class Filter(BaseModel):
    field: str
    value: str
    method: FilterMethod = FilterMethod.contains

    class Config:
        use_enum_values = True


class FiltersConfig(BaseModel):
    commit: list[Filter] = None


class DefaultsConfig(BaseModel):
    delete_clone: bool = False
    index_file_modifications: bool = False
    pydriller_filters: PydrillerConfig = None
    filters: FiltersConfig = None


class RepositoryConfig(DefaultsConfig):
    name: str
    url: str = None

    delete_clone: bool = None
    index_file_modifications: bool = None


class DrillConfig(BaseModel):
    defaults: DefaultsConfig
    repositories: list[RepositoryConfig]


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
        items.append(
            JobList(
                id=job.id, name=job.name, data=job.data, status=latest_status.status
            )
        )
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


@router.post("/jobs/", response_model=list[JobList])
async def create_job(
    *,
    session: Session = Depends(get_session),
    drill_config: DrillConfig,
    background_tasks: BackgroundTasks,
    request: Request
):
    drill_config_dict = drill_config.model_dump()
    jobs_list = []
    for repo_config in drill_config_dict["repositories"]:
        logger.warning(repo_config)
        # job_dict = {
        #     "defaults": drill_config.defaults.model_dump_json(),
        #     "repository": repo_config.model_dump_json(),
        # }
        job_dict = {
            "defaults": drill_config_dict["defaults"],
            "repository": repo_config,
        }

        db_job = Job.model_validate(JobCreate(name=repo_config["name"], data=job_dict))

        session.add(db_job)
        session.commit()
        session.refresh(db_job)

        db_job_status = JobStatus(job_id=db_job.id)
        session.add(db_job_status)
        session.commit()
        session.refresh(db_job_status)

        # background_tasks.add_task(
        #     request.state.driller_client.call,
        #     json.dumps(job_dict),
        # )

        job, status = get_job_status(session, db_job.id)

        jobs_list.append(
            JobList(id=job.id, name=job.name, data=job.data, status=status.status)
        )

    # result = await driller_client.call(body)
    return jobs_list
    # return Response(jobs_list, status_code=201)
