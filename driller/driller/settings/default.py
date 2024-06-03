import logging
import os

DATE_FORMAT = "%d %B, %Y %H:%M"

PIKA_HOST = os.environ.get("PIKA_HOST")
PIKA_PORT = os.environ.get("PIKA_PORT")
PIKA_QUEUE = os.environ.get("PIKA_QUEUE")

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

REPO_CLONE_LOCATION = ""

DEFAULT_CONFIGS = {
    "DRILLER_CLASS": "driller.config_driller.ConfigDriller",
    "WORKER_CLASS": "driller.workers.queue_driller_worker.QueueDrillerWorker"
}

CONFIGS = {**DEFAULT_CONFIGS}



