import logging
import os

DATE_FORMAT = "%d %B, %Y %H:%M"

PIKA_HOST = os.environ.get("PIKA_HOST")
PIKA_PORT = os.environ.get("PIKA_PORT")
PIKA_QUEUE = os.environ.get("PIKA_QUEUE")

NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
NEO4J_HOST = os.environ.get("NEO4J_HOST")
NEO4J_PORT = os.environ.get("NEO4J_PORT")
NEO4J_DEFAULT_BATCH_SIZE = os.environ.get("NEO4J_DEFAULT_BATCH_SIZE")

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

REPO_CLONE_LOCATION = ""

DEFAULT_CONFIGS = {
    "DRILLER_CLASS": "driller.config_driller.ConfigDriller",
    "WORKER_CLASS": "driller.workers.queue_driller_worker.QueueDrillerWorker"
}

CONFIGS = {**DEFAULT_CONFIGS}



