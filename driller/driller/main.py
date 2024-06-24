#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys

from driller.util import get_class

from driller.settings.default import (
    LOG_FORMAT,
    LOG_LEVEL,
    CONFIGS,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_QUEUE,
    NEO4J_HOST,
    NEO4J_PORT,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_DEFAULT_BATCH_SIZE,
)
from driller.workers.queue_worker import QueueWorker, Worker

logger = logging.getLogger(__name__)
logging.getLogger("pydriller").setLevel(logging.WARNING)

worker: Worker | None = None


def exit_signal_handler(*_):
    if worker is not None:
        worker.close()
    sys.exit(0)


async def main():
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

    pika_logger = logging.getLogger("pika")
    pika_logger.setLevel(logging.WARNING)

    signal.signal(signal.SIGINT, signal_handler)
    # Catch the docker container stop to speed up shutdown
    signal.signal(signal.SIGTERM, signal_handler)

    # Retrive the classes that will be used from the settings configuration.
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

    await worker.start()


def exec():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
