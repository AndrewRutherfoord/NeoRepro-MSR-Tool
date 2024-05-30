#!/usr/bin/env python3

from dataclasses import asdict, dataclass
import signal
import sys

import pika

from driller.cloner import clone_repository
from driller.config_driller import (
    ConfigDriller,
)

from common.driller_config import DrillConfig


from driller.settings import (
    LOG_FORMAT,
    PIKA_HOST,
    PIKA_PORT,
    PIKA_QUEUE,
    config_logging,
)

logger = config_logging()

worker = None

from abc import ABC, abstractmethod


class QueueWorker(ABC):

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port)
            )
            self.channel = self.connection.channel()
        except:
            logger.exception("Could not connect to message queue.")

    @abstractmethod
    def on_request(ch, method, props, body):
        pass

    def consume_jobs(self, queue):
        self.channel.queue_declare(queue=PIKA_QUEUE)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=PIKA_QUEUE, on_message_callback=self.on_request)

        logger.info(f"Awaiting Tasks on queue '{queue}'.")
        self.channel.start_consuming()

    def close(self):
        self.connection.close()


class QueueDrillerWorker(QueueWorker):

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
        driller = ConfigDriller(conf.neo, project)

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


def signal_handler(sig, frame):
    worker.close()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    worker = QueueDrillerWorker(host=PIKA_HOST, port=PIKA_PORT)
    worker.connect()
    worker.consume_jobs(PIKA_QUEUE)


if __name__ == "__main__":
    main()
