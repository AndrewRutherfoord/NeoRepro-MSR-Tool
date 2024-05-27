import json
import logging
from datetime import datetime
from dataclasses import asdict, dataclass, fields
from neo4j import GraphDatabase

from graphrepo.config import Config
from graphrepo.drillers.driller import Driller

from driller.cloner import clone_repository
from driller.settings import DATE_FORMAT, REPO_CLONE_LOCATION


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "neo4j123")

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # Convert datetime object to a string
            return obj.strftime(DATE_FORMAT)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

@dataclass
class Neo4jConfig:
    db_url: str
    db_user: str
    db_pwd: str
    port: int = 7687
    batch_size: int = 50

    def __dict__(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: dict):
        return Neo4jConfig(**data)


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
    url: str = None

    def __init__(self, repo=None, project_id=None, url=None, **kwargs):
        super().__init__(**kwargs)
        self.repo=REPO_CLONE_LOCATION+repo
        self.project_id = project_id
        self.url = url

    def __dict__(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: dict):
        return ProjectConfig(**data)
    
@dataclass
class DrillConfig:
    neo: Neo4jConfig
    project: ProjectConfig

    def __dict__(self):
        return {
            "neo": self.neo.__dict__(),
            "project": self.project.__dict__(),
        }

    def to_json(self):
        return json.dumps(self.__dict__(), cls=DateTimeEncoder)
    
    @staticmethod
    def from_json(data: str) -> "DrillConfig":
        data = json.loads(data)
        
        project_data = data["project"]
        project_data["start_date"] = datetime.strptime(project_data["start_date"], DATE_FORMAT)
        project_data["end_date"] = datetime.strptime(project_data["end_date"], DATE_FORMAT)

        neo_data = data["neo"]
        
        return DrillConfig(
            project=ProjectConfig(**project_data),
            neo=Neo4jConfig(**neo_data),
        )


def apply_defaults(project: ProjectConfig, defaults: ProjectDefaults):
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
            logger.exception(exc)


# def drill_repositories(
#     projects: list[ProjectConfig], neo: Neo4jConfig, project_defaults: ProjectDefaults
# ):
#     logger.debug(project_defaults)

#     project_applied_defaults = []
#     for project in projects:
#         p = apply_defaults(project, defaults=project_defaults)
#         if project.url:
#             clone_repository(
#                 repository_url=project.url, repository_location=project.repo
#             )
#         project_applied_defaults.append(p)

#     for project in project_applied_defaults:
#         execute_repository_drill_job(neo, project)
