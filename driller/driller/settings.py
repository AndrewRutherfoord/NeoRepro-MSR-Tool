import logging
import os

DATE_FORMAT = "%d %B, %Y %H:%M"

PIKA_HOST = os.environ.get("PIKA_HOST")
PIKA_PORT = os.environ.get("PIKA_PORT")
PIKA_QUEUE = os.environ.get("PIKA_QUEUE")

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

REPO_CLONE_LOCATION = ""

def config_logging():

    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)

    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(LOG_LEVEL)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    pika_logger = logging.getLogger("pika")
    pika_logger.setLevel(logging.WARNING)

    return logger   
