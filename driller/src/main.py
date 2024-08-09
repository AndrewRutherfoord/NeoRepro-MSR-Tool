#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys

from src.util import get_class

from src.settings.default import (
    LOG_FORMAT,
    LOG_LEVEL,
    CONFIGS,
    RABBITMQ_LOG_LEVEL,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_QUEUE,
    NEO4J_LOG_LEVEL,
    NEO4J_HOST,
    NEO4J_PORT,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DEFAULT_BATCH_SIZE,
)
from src.workers.queue_worker import QueueWorker, Worker

logger = logging.getLogger(__name__)
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
std_out_handler = logging.StreamHandler(sys.stdout)

pika_logger = logging.getLogger("pika")
pika_logger.setLevel(RABBITMQ_LOG_LEVEL)
pika_logger.addHandler(std_out_handler)

neo4j_logger = logging.getLogger("neo4j")
neo4j_logger.setLevel(NEO4J_LOG_LEVEL)
neo4j_logger.addHandler(std_out_handler)

"""
This is the main file of the driller worker. 
It creates in instance of the driller worker that is set in the settings file and the waits for queue to have drill jobs to complete.
"""

worker: Worker | None = None


async def main():
    storage_class = get_class(CONFIGS.get("REPOSITORY_STORAGE_CLASS"))
    driller_class = get_class(CONFIGS.get("REPOSITORY_DRILLER_CLASS"))
    worker_class = get_class(CONFIGS.get("WORKER_CLASS"))

    worker: QueueWorker = worker_class(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        user=RABBITMQ_USER,
        password=RABBITMQ_PASSWORD,
        queue_name=RABBITMQ_QUEUE,
        driller_class=driller_class,
        storage_class=storage_class,
        storage_args={
            "host": NEO4J_HOST,
            "port": NEO4J_PORT,
            "user": NEO4J_USER,
            "password": NEO4J_PASSWORD,
            "batch_size": NEO4J_DEFAULT_BATCH_SIZE,
        },
    )
    loop = asyncio.get_running_loop()

    # Signal handler to gracefully shut down the worker
    def signal_handler():
        logger.info("Received termination signal, shutting down gracefully...")
        if worker is not None:
            asyncio.create_task(worker.close())
        for task in asyncio.all_tasks(loop):
            task.cancel()

    loop.add_signal_handler(signal.SIGTERM, signal_handler)
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    await worker.start()


def exec():
    asyncio.run(main())


if __name__ == "__main__":
    exec()
