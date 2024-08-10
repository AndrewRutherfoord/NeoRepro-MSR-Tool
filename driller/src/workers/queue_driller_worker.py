import json
import logging

import aio_pika
from pydantic import ValidationError

from src.cloner import clone_repository, remove_repository_clone

from src.drillers.driller import RepositoryDriller

from src.settings.default import (
    REPO_CLONE_LOCATION,
)
from .queue_worker import QueueWorker

from common.models.driller_config import SingleDrillConfig, RepositoryConfig

logger = logging.getLogger(__name__)


class QueueRepositoryNeo4jDrillerWorker(QueueWorker):

    def __init__(
        self,
        host,
        port,
        user,
        password,
        queue_name,
        driller_class,
        storage_class,
        driller_args: dict = {},
        storage_args: dict = {},
        clone_location: str = REPO_CLONE_LOCATION,
    ):
        super().__init__(host, port, user, password, queue_name)

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
        """Uses the storage and repository driller passed as parameters to class to perform drilling.
        Clones repository if needed.

        Args:
            drill_config (SingleDrillConfig): COnfiguration that defines the drill job.

        Raises:
            LookupError: When repository can't be cloned
            Exception:
        """
        storage = None
        try:
            # Apply defaults to the repository config
            repository: RepositoryConfig = drill_config.repository
            if drill_config.defaults:
                repository.apply_defaults(drill_config.defaults)

            # Set path to clone or find repo based on location where repo clones are stored in container.
            repo_path = f"{self.clone_location}/{repository.name}"

            # Clone Repository if url exists. Throws `LookupError` if problem cloning repo.
            if repository.url is not None:
                clone_repository(
                    repository_url=repository.url, repository_location=repo_path
                )
                logger.debug(f"Cloned Repository {repository.name} to `{repo_path}`")

            # Instantiate the storage class where the drilled data will be written to.
            storage = self.storage_class(**self.storage_args)

            # Instantiate the driller class. Drills the repository and writes the data to the storage class.
            driller: RepositoryDriller = self.driller_class(
                repository_path=repo_path,
                storage=storage,
                config=repository,
                **self.driller_args,
            )

            # Preform the drill job.
            driller.drill_repository()
            driller.drill_commits(
                filters=repository.filters,
                pydriller_filters=repository.pydriller,
            )

            # Cleanup
            storage.close()

            if repository.delete_clone:
                remove_repository_clone(repo_path)

        except LookupError as e:
            raise e
        except Exception as e:
            logger.exception(e)
            if storage is not None:
                storage.close()
            raise e

    def parse_message(self, message: str) -> SingleDrillConfig:
        """Parses the incoming message string to a SingleDrillerConfig model.

        Args:
            message (str): The string to be parsed.
        Raises:
            ValidationError: Thrown when the config received does not match the schema.
        Returns:
            SingleDrillConfig: Parsed config in a pytantic model instance.
        """
        try:
            return SingleDrillConfig.model_validate_json(message)
        except ValidationError as e:
            logger.exception(e)
            raise e

    async def on_before_start_job(
        self, job_body, message: aio_pika.abc.AbstractIncomingMessage
    ):
        """Method that is executed before drilling job starts. Sends response saying that drilling is started.

        Args:
            job_body (str): Job COnfig to be parsed by `parse_message`
            message (aio_pika.abc.AbstractIncomingMessage): Pika Message to be used to send response to creator of message.
        """
        if message.reply_to is None:
            raise ValueError("Message must contain a `reply_to` field.")

        drill_config = self.parse_message(job_body)

        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    {
                        "status": "started",
                        "job_id": drill_config.job_id,
                        "message": "Drilling started.",
                    }
                ).encode(),
                correlation_id=message.correlation_id,
            ),
            routing_key=message.reply_to,
        )

    def create_response(self, job_id, message, status):
        """Creates the standard response that is used for this driller.

        Args:
            job_id (int): Some id to identify the job
            message (str): Response message
            status (str): Response status (complete, started, failed)

        Returns:
            dict: response dictionary
        """
        return {
            "status": status,
            "job_id": job_id,
            "message": message,
        }

    def create_error_response(self, job_id, message):
        """Creates an error response using `create_response`"""
        return self.create_response(job_id, message, "failed")

    def on_request(
        self, body: str, message: aio_pika.abc.AbstractIncomingMessage
    ) -> str:
        """Performs the repository drill job on receiving job config from RabbitMQ.

        Args:
            body (str): Body of message received from RabbitMQ. Contains JSON.
            message (AbstractIncomingMessage): AIO Pika message used for sending responses.

        Returns:
            str: json string to send as a response
        """

        job_id = None
        drill_config: SingleDrillConfig | None = None
        response = {}
        try:
            drill_config = self.parse_message(body)
            job_id = drill_config.job_id

            logger.info(f"Starting Drill Job: {drill_config.repository.name}")

            self.execute_drill_job(drill_config)

            response = self.create_response(job_id, "Drilling complete.", "complete")
            logger.info(f"Drill Job Complete: {drill_config.repository.name}")

        except LookupError:
            response = self.create_error_response(
                job_id, "Repository not found on remote host."
            )
        except ValidationError:
            response = self.create_error_response(job_id, "Drill config invalid.")
        except Exception as e:
            logger.exception(e)
            if drill_config is None:
                logger.error(f"Drill Job Failed: {body}")
            else:
                logger.error(f"Drill Job Failed: {drill_config.repository.name}")
            response = self.create_error_response(job_id, f"Drilling failed: {str(e)}")
        return json.dumps(response)
