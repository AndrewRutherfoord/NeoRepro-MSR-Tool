import logging

DATE_FORMAT = "%d %B, %Y %H:%M"

PIKA_HOST = "localhost"
PIKA_PORT = 5672
PIKA_QUEUE = "driller_queue"

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def config_logging():

    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)

    logger = logging.getLogger(__name__)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    pika_logger = logging.getLogger("pika")
    pika_logger.setLevel(logging.WARNING)

    return logger
