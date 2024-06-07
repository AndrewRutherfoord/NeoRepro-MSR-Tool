import logging
from typing import Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

logger = logging.getLogger(__name__)

class JobBase(SQLModel):
    name: str
    data : dict = Field(sa_column=Column(JSON), default={})

class Job(JobBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
class JobCreate(JobBase):
    pass

class JobDetails(JobBase):
    pass