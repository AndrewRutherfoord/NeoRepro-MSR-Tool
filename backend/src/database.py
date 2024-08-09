import logging
from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

# Configuring database connection to sqlite.
# Database migrations are handled by Alembic. If any changed are made to the database models
# then consult backend README about how to migrate.

sqlite_file_name = "database.sqlite"
sqlite_url = f"sqlite:///src/{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def get_session():
    """Dependency that is injected into endpoints for DB access"""
    with Session(engine) as session:
        yield session
