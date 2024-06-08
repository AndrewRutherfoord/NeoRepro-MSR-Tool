import logging
from typing import Optional
from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel, create_engine, select

logger = logging.getLogger(__name__)

sqlite_file_name = "database.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    logger.warning("Creating tables.")
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
