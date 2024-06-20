import json
import logging

import aio_pika
from pydantic import ValidationError

from driller.cloner import clone_repository

from driller.drillers.driller import RepositoryDriller
from driller.drillers.storage import RepositoryNeo4jStorage

from driller.settings.default import (
    REPO_CLONE_LOCATION,
)
from driller.util import remove_none_values
from .queue_worker import QueueWorker

from common.models.driller_config import SingleDrillConfig, RepositoryConfig

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

    def execute_drill_job(self, drill_config: SingleDrillConfig):

        repository: RepositoryConfig = drill_config.repository
        repository.apply_defaults(drill_config.defaults)

        repo_path = f"{self.clone_location}{repository.name}"

        if repository.url is not None:
            clone_repository(
                repository_url=repository.url, repository_location=repo_path
            )
            logger.debug(f"Cloned Repository {repository.name} to `{repo_path}`")

        # Instantiate the storage class where the drilled data will be written
        storage = self.storage_class(**self.storage_args)

        # Instantiate the driller class. Drills the repository and writes the data to the storage class.
        driller: RepositoryDriller = self.driller_class(
            repository_path=repo_path,
            storage=storage,
            config=repository,
            **self.driller_args,
        )

        try:
            driller.drill_repository()
            driller.drill_commits(
                filters=repository.filters,
                pydriller_filters=repository.pydriller,
            )
            storage.close()
        except Exception as e:
            logger.exception(e)
            storage.close()
            raise e

    def parse_message(self, message) -> SingleDrillConfig:
        try:
            return SingleDrillConfig.model_validate_json(message)
        except ValidationError as e:
            logger.exception(e)
            raise e

    async def on_before_start_job(
        self, job_body, message: aio_pika.abc.AbstractIncomingMessage
    ):
        drill_config = self.parse_message(job_body)

        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps({
                    "status": "started",
                    "job_id": drill_config.job_id,
                    "message": "Drilling started.",
                }).encode(),
                correlation_id=message.correlation_id,
            ),
            routing_key=message.reply_to,
        )

    def on_request(self, body, message):
        job_id = None
        try:
            drill_config = self.parse_message(body)
            job_id = drill_config.job_id
            logger.info(f"Starting Drill Job: {drill_config.repository.name}")
            try:
                self.execute_drill_job(drill_config)
                response = {
                    "status": "complete",
                    "job_id": job_id,
                    "message": "Drilling complete.",
                }
                logger.info(f"Drill Job Complete: {drill_config.repository.name}")
            except Exception as e:
                logger.exception(e)
                logger.error(f"Drill Job Failed: {drill_config.repository.name}")
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
