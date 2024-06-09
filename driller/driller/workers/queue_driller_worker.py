import logging

import pika

from driller.cloner import clone_repository
from driller.drillers.driller import (
    ConfigDriller,
    RepositoryDataStorage,
)
from driller.settings.default import (
    NEO4J_DEFAULT_BATCH_SIZE,
    NEO4J_HOST,
    NEO4J_PORT,
    NEO4J_USER,
    NEO4J_PASSWORD,
)
from driller.util import get_class
from ..driller_config import DrillConfig, Neo4jConfig
from .queue_worker import QueueWorker

logger = logging.getLogger(__name__)


class QueueDrillerWorker(QueueWorker):

    def __init__(self, host, port, queue, driller_class, storage : RepositoryDataStorage):
        super().__init__(host, port, queue)

        self.driller_class = driller_class
        self.storage = storage

    def execute_drill_job(self, conf: DrillConfig):
        project = conf.project
        if project.url:
            clone_repository(
                repository_url=project.url, repository_location=project.repo
            )
        logger.info(
            f"Drilling {project.project_id} between {project.start_date} and {project.end_date}"
        )
        logger.debug(f"{ project.repo }")

        # Instantiate instance of driller class
        driller = self.driller_class(conf.neo, project)

        try:
            driller.init_db()
        except Exception as exc:
            print("DB already initialized")

        driller.drill_batch()
        driller.merge_all()

    def on_request(self, body):
        try:
            # Repo base location is where the cloned repos are stored or where they should be clone to.
            drill_job = DrillConfig.from_json(
                body, repo_base_location="/app/driller/repos/"
            )

            # If neo setup isn't set then set from environment variables.
            if drill_job.neo is None:
                drill_job.neo = self.get_env_neo()

            logger.info(f"Received Drill Job: {drill_job.project.project_id}")
            logger.info(drill_job.neo.__dict__())
            
            self.execute_drill_job(drill_job)

            logger.info(f"Drill Job Complete: {drill_job.project.project_id}")

            response = f"Drilling Complete for project {drill_job.project.project_id}."
            return response
        except Exception as e:
            logger.exception(e)
