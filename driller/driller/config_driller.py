import logging
from dataclasses import asdict

from graphrepo.config import Config
from graphrepo.drillers.driller import Driller

from common.driller_config import Neo4jConfig, ProjectConfig

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "neo4j123")

logger = logging.getLogger(__name__)

class ConfigDriller(Driller):
    """A GraphRepo Driller that takes configs from config objects."""

    def __init__(self, neoConf: Neo4jConfig, projectConf: ProjectConfig):
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
