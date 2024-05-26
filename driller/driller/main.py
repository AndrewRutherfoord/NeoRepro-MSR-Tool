#!/usr/bin/env python3

from dataclasses import asdict, dataclass
import logging
import time

import pika

from driller.cloner import clone_repository
from driller.config_driller import (
    DrillConfig,
    execute_repository_drill_job,
)
from driller.settings import LOG_FORMAT, PIKA_HOST, PIKA_PORT, PIKA_QUEUE, config_logging

logger = config_logging()

def execute_drill_job(conf: DrillConfig):
    if conf.project.url:
        clone_repository(
            repository_url=conf.project.url, repository_location=conf.project.repo
        )
    execute_repository_drill_job(conf.neo, conf.project)


def on_request(ch, method, props, body):
    try:
        drill_job = DrillConfig.from_json(body)

        logger.info(f"Received Drill Job: {drill_job.project.project_id}")

        execute_drill_job(drill_job)

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


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=PIKA_HOST, port=PIKA_PORT)
    )

    channel = connection.channel()

    channel.queue_declare(queue=PIKA_QUEUE)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=PIKA_QUEUE, on_message_callback=on_request)

    logger.info("Awaiting Drill Tasks")
    channel.start_consuming()

    # conf = load_yaml("driller/configs/test.yaml")
    # neo, defaults, projects = parse_config(conf)
    # drill_repositories(neo=neo, projects=projects, project_defaults=defaults)


if __name__ == "__main__":
    main()
