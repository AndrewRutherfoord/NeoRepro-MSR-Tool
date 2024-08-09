import logging
import time

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlmodel import Session

from common.models.jobs import (
    JobStatus,
    JobStatusDetails,
)

from src.database import get_session
from src.ws_connection_manager import socket_connections

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()


@router.websocket("/jobs/statuses/")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
):
    await socket_connections.connect(websocket)
    logger.warning("WS COnnect")
    try:
        while True:
            logger.info(socket_connections)
            text = await websocket.receive_text()  # not really necessary
            logger.info(f"Received text: {text}")

    except WebSocketDisconnect:
        socket_connections.disconnect(websocket)


@router.post("/jobs/status/")
def create_job_status(
    *, session: Session = Depends(get_session), job_status: JobStatus
):
    """Creates a Job Status in the database. Mostly for testing as the
    job statuses should be created based on reponses from the workers"""
    session.add(job_status)
    session.commit()
    session.refresh(job_status)
    return job_status


@router.get("/jobs/status/{job_status_id}", response_model=JobStatusDetails)
def detail_job_status(*, session: Session = Depends(get_session), job_status_id: int):
    """Get a particular job status based on the id"""
    job_status = session.get(JobStatus, job_status_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status
