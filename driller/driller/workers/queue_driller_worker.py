import logging

import pika

from driller.cloner import clone_repository
from driller.config_driller import (
    ConfigDriller,
)
from driller.util import get_class
from ..driller_config import DrillConfig
from .queue_worker import QueueWorker

logger = logging.getLogger(__name__)

class QueueDrillerWorker(QueueWorker):
    
    def __init__(self, host, port, queue, driller_class):
        super().__init__(host, port, queue)
        
        self.driller_class = driller_class


    def execute_drill_job(self, conf: DrillConfig):
        project = conf.project
        if project.url:
            clone_repository(
                repository_url=project.url, repository_location=project.repo
            )
        logger.info(
            f"Drilling {project.project_id} between {project.start_date} and {project.end_date}"
        )
        logger.debug(
            f"{ project.repo }"
        )

        # Instantiate instance of driller class
        driller = self.driller_class(conf.neo, project)

        try:
            driller.init_db()
        except Exception as exc:
            print("DB already initialized")
        
        driller.drill_batch()
        driller.merge_all()

    def on_request(self, ch, method, props, body):
        try:
            drill_job = DrillConfig.from_json(body, repo_base_location="/app/driller/repos/")

            logger.info(f"Received Drill Job: {drill_job.project.project_id}")

            self.execute_drill_job(drill_job)

            logger.info(f"Drill Job Complete: {drill_job.project.project_id}")

            response = f"Drilling Complete for project {drill_job.project.project_id}."
            ch.basic_publish(
                exchange="",
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=str(response),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.exception(e)