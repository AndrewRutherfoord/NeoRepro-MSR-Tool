#!/usr/bin/env python3

import logging
import signal
import sys

from driller.settings.default import LOG_FORMAT, LOG_LEVEL, CONFIGS
from driller.util import get_class

from driller.settings.default import (
    PIKA_HOST,
    PIKA_PORT,
    PIKA_QUEUE,
)

logger = logging.getLogger(__name__)

worker = None


def signal_handler(sig, frame):
    worker.close()
    sys.exit(0)


def main():
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

    pika_logger = logging.getLogger("pika")
    pika_logger.setLevel(logging.WARNING)

    signal.signal(signal.SIGINT, signal_handler)
    # Catch the docker container stop to speed up shutdown
    signal.signal(signal.SIGTERM, signal_handler)

    driller_class = get_class(CONFIGS.get("DRILLER_CLASS"))
    worker_class = get_class(CONFIGS.get("WORKER_CLASS"))

    worker = worker_class(host=PIKA_HOST, port=PIKA_PORT, queue=PIKA_QUEUE, driller_class=driller_class)
    worker.connect()
    worker.consume_jobs()


if __name__ == "__main__":
    main()
