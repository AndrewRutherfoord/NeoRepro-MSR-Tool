import json
from datetime import datetime
from dataclasses import asdict, dataclass, fields

from .settings.default import DATE_FORMAT


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
        return Neo4jConfig(
            **data,
            port=int(data.get("port")),
            batch_size=int(data.get("batch_size")),
        )


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

    def __init__(
        self, repo=None, project_id=None, url=None, base_location="", **kwargs
    ):
        super().__init__(**kwargs)
        self.repo = base_location + repo
        self.project_id = project_id
        self.url = url

    def __dict__(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: dict, base_location=""):
        return ProjectConfig(repo=base_location + data.pop("repo", ""), **data)


@dataclass
class DrillConfig:
    neo: Neo4jConfig
    project: ProjectConfig

    def __dict__(self):
        return {
            "neo": self.neo.__dict__() if self.neo else None,
            "project": self.project.__dict__(),
        }

    def to_json(self):
        return json.dumps(self.__dict__(), cls=DateTimeEncoder)

    @staticmethod
    def from_json(data: str, repo_base_location="") -> "DrillConfig":
        data = json.loads(data)

        project_data = data["project"]
        project_data["start_date"] = datetime.strptime(
            project_data["start_date"], DATE_FORMAT
        )
        project_data["end_date"] = datetime.strptime(
            project_data["end_date"], DATE_FORMAT
        )

        neo = None
        if data.get("neo", None) is not None:
            neo = Neo4jConfig(**data["neo"])

        return DrillConfig(
            project=ProjectConfig(**project_data, base_location=repo_base_location),
            neo=neo,
        )


def apply_defaults(project: ProjectConfig, defaults: ProjectDefaults):
    for field in fields(ProjectDefaults):
        if getattr(project, field.name) is None:
            setattr(project, field.name, getattr(defaults, field.name))
    return project
