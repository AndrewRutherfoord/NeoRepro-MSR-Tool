import logging
from dataclasses import asdict

from graphrepo.config import Config
from graphrepo.drillers.driller import Driller

from driller.cloner import clone_repository
from driller.util import load_yaml, parse_config

from driller.driller_config import DrillConfig, Neo4jConfig, ProjectConfig, ProjectDefaults, apply_defaults

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
