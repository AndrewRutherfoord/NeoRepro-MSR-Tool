import json
import logging

import pika

from driller.cloner import clone_repository
from driller.drillers.driller import (
    RepositoryDataStorage,
)

from driller.drillers.driller import RepositoryDriller
from driller.drillers.storage import RepositoryNeo4jStorage

from driller.settings.default import (
    NEO4J_DEFAULT_BATCH_SIZE,
    NEO4J_HOST,
    NEO4J_PORT,
    NEO4J_USER,
    NEO4J_PASSWORD,
)
from driller.util import get_class, remove_none_values
from ..driller_config import DrillConfig, Neo4jConfig
from .queue_worker import QueueWorker

logger = logging.getLogger(__name__)

class QueueRepositoryNeo4jDrillerWorker(QueueWorker):

    def __init__(
        self,
        host,
        port,
        queue,
        driller_class,
        storage_class,
        driller_args: dict = {},
        storage_args: dict = {},
    ):
        super().__init__(host, port, queue)

        self.driller_class = driller_class
        self.driller_args = driller_args
        self.storage_class = storage_class
        self.storage_args = storage_args

    def apply_defaults(self, defaults: dict, repository: dict):
        for key, value in defaults.items():
            if repository.get(key, None) is None:
                repository[key] = value
        return repository

    def execute_drill_job(self, defaults, repository):

        repository = self.apply_defaults(defaults, repository)

        if "path" in repository:
            raise ValueError("Path cannot be set outside driller.")

        repository["path"] = f"app/driller/repos/{repository['name']}"

        logger.info("---------- Defaults Applied ----------")

        if repository.get("url", None) is not None:
            clone_repository(
                repository_url=repository["url"], repository_location=repository["path"]
            )
            logger.info("---------- Repository Cloned ----------")

        # # Instantiate instance of driller class
        storage = self.storage_class(**self.storage_args)
        driller = self.driller_class(
            repository_path=repository["path"], storage=storage, **self.driller_args
        )
        logger.info("---------- Driller Instantiated ----------")

        driller.drill_repository()
        driller.drill_commits(
            filters=repository.get("filters", {}),
            pydriller_filters=remove_none_values(repository.get("pydriller", {})),
        )

        storage.close()

    def on_request(self, body):
        try:
            data = json.loads(body)

            self.execute_drill_job(data.get("defaults"), data.get("repository"))

            # logger.info(f"Drill Job Complete: {drill_job.project.project_id}")

            response = f"Drilling Complete for project ."
            return response
        except Exception as e:
            logger.exception(e)
            return "Error: Could not process job."
