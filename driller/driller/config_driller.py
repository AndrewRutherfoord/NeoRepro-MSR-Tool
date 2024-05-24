import logging
from datetime import datetime
from dataclasses import asdict, dataclass, fields
from neo4j import GraphDatabase

from graphrepo.config import Config
from graphrepo.drillers.driller import Driller

from driller.cloner import clone_repository


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "neo4j123")

logging.basicConfig(level=logging.INFO)


@dataclass
class Neo4jConfig:
    db_url: str
    db_user: str
    db_pwd: str
    port: int = 7687
    batch_size: int = 50


@dataclass(kw_only=True)
class ProjectDefaults:
    index_code: bool = None
    index_developer_email: bool = None
    start_date: str = None
    end_date: str = None


@dataclass(kw_only=True)
class ProjectConfig(ProjectDefaults):
    repo: str
    project_id: str
    url: str  =None
    
def apply_defaults(project : ProjectConfig, defaults : ProjectDefaults):
    for field in fields(ProjectDefaults):
        if getattr(project, field.name) is None:
            setattr(project, field.name, getattr(defaults, field.name))
    return project


class ConfigDriller(Driller):

    def __init__(self, neoConf: Neo4jConfig, projectConf: ProjectConfig):
        """Initializes the properties of this class
        :param config_path: path to yml config file
        """
        try:
            neo = asdict(neoConf)
            project = asdict(projectConf)
            self.config = Config()
            self.graph = None
            self.config.configure(**neo, **project)
            self._connect()
        except Exception as exc:
            logging.exception(exc)


# Mines a specified repository based on the project configurations
def execute_repository_drill_job(neo: Neo4jConfig, project: ProjectConfig):
    logging.info(f"Drilling {project.project_id} between {project.start_date} and {project.end_date}")
    driller = ConfigDriller(neo, project)
    try:
        driller.init_db()
    except Exception as exc:
        print("DB already initialized")
    driller.drill_batch() 
    driller.merge_all()


def set_defaults(project : ProjectConfig, defaults: ProjectDefaults):
    pass

def drill_repositories(
    projects: list[ProjectConfig], neo: Neo4jConfig, project_defaults: ProjectDefaults
):
    logging.debug(project_defaults)

    project_applied_defaults = []
    for project in projects:
        p = apply_defaults(project, defaults=project_defaults)
        clone_repository(repository_url=project.url, repository_location=project.repo)
        project_applied_defaults.append(p)
    
    for project in project_applied_defaults:
        execute_repository_drill_job(neo, project)
