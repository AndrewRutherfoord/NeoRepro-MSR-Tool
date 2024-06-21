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
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from common.models.jobs import (
    Job,
    JobBase,
    JobCreate,
    JobDetails,
    JobList,
    JobStatus,
    JobStatusDetails,
    JobStatusOverview,
)

from backend.database import get_session
from backend.ws_connection_manager import socket_connections

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()


@router.websocket("/jobs/statuses/")
async def websocket_endpoint(
    *,
    websocket: WebSocket,
):
    # TODO: Some key??
    ws_token = "1"
    await socket_connections.connect(websocket, ws_token=ws_token)
    try:
        while True:
            logger.info(socket_connections)
            text = await websocket.receive_text()  # not really necessary
            logger.info(f"Received text: {text}")

    except WebSocketDisconnect:
        socket_connections.disconnect(websocket, ws_token=ws_token)


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