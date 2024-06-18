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
    REPO_CLONE_LOCATION,
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
        queue_name,
        driller_class,
        storage_class,
        driller_args: dict = {},
        storage_args: dict = {},
        clone_location: str = REPO_CLONE_LOCATION,
    ):
        super().__init__(host, port, queue_name)

        self.driller_class = driller_class
        self.driller_args = driller_args
        self.storage_class = storage_class
        self.storage_args = storage_args
        
        self.clone_location = clone_location

    def apply_defaults(self, defaults: dict, repository: dict):
        for key, value in defaults.items():
            if repository.get(key, None) is None:
                repository[key] = value
        return repository

    def execute_drill_job(self, defaults, repository):

        repository = self.apply_defaults(defaults, repository)

        if "path" in repository:
            logger.error("Path cannot be set outside driller.")
            raise ValueError("Path cannot be set outside driller.")

        repository["path"] = f"{self.clone_location}{repository['name']}"

        if repository.get("url", None) is not None:
            clone_repository(
                repository_url=repository["url"], repository_location=repository["path"]
            )
            logger.debug(
                f"Cloned Repository {repository['name']} to `{repository['path']}`"
            )

        # Instantiate the storage class where the drilled data will be written
        storage = self.storage_class(**self.storage_args)

        # Instantiate the driller class. Drills the repository and writes the data to the storage class.
        driller: RepositoryDriller = self.driller_class(
            repository_path=repository["path"],
            storage=storage,
            config=repository,
            **self.driller_args,
        )

        try:
            driller.drill_repository()
            driller.drill_commits(
                filters=repository.get("filters", {}),
                pydriller_filters=remove_none_values(repository.get("pydriller", {})),
            )
            storage.close()
        except Exception as e:
            logger.exception(e)
            storage.close()
            raise e

    def on_request(self, body):
        try:
            data = json.loads(body)
            job_id = data.get("job_id")
            logger.info(f"Starting Drill Job: {data.get('name')}")
            try:
                self.execute_drill_job(data.get("defaults"), data.get("repository"))
                response = {
                    "status": "complete",
                    "job_id": job_id,
                    "message": "Drilling complete.",
                }
                logger.info(f"Drill Job Complete: {data.get('name')}")
            except Exception as e:
                logger.error(f"Drill Job Failed: {data.get('name')}")
                response = {
                    "status": "failed",
                    "job_id": job_id,
                    "message": "Drilling failed.",
                }
            return json.dumps(response)

            # response = f"Drilling Complete for job `{job_id}` ."
        except Exception as e:
            logger.exception(e)
            return json.dumps(
                {
                    "status": "failed",
                    "job_id": job_id,
                    "message": "Drilling failed.",
                }
            )
