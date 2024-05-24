import logging
from datetime import datetime
from dataclasses import asdict, dataclass, fields
from neo4j import GraphDatabase

from graphrepo.config import Config
from graphrepo.drillers.driller import Driller


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
    start_date: str = datetime.strptime("1 February, 2021 00:00", '%d %B, %Y %H:%M')
    end_date: str = datetime.strptime("30 March, 2021 00:00", '%d %B, %Y %H:%M')


@dataclass(kw_only=True)
class ProjectConfig(ProjectDefaults):
    repo: str
    project_id: str
    
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
    logging.info(project)
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
    for project in projects:
        p = apply_defaults(project, defaults=project_defaults)
        execute_repository_drill_job(neo, p)
