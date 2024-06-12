import logging
import os

# DATE_FORMAT = "%d %B, %Y %H:%M"
DATE_FORMAT = "%Y-%m-%d"

PIKA_HOST = os.environ.get("PIKA_HOST")
PIKA_PORT = os.environ.get("PIKA_PORT")
PIKA_QUEUE = os.environ.get("PIKA_QUEUE")

AUTO_ACKNOWLEDGE = os.environ.get("AUTO_ACKNOWLEDGE") in ["1", "true", "True"]

NEO4J_USER = os.environ.get("NEO4J_USER", None)
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", None)
NEO4J_HOST = os.environ.get("NEO4J_HOST", None)
NEO4J_PORT = os.environ.get("NEO4J_PORT", None)
NEO4J_DEFAULT_BATCH_SIZE = None
if os.environ.get("NEO4J_DEFAULT_BATCH_SIZE", None) is not None:
    NEO4J_DEFAULT_BATCH_SIZE = int(os.environ.get("NEO4J_DEFAULT_BATCH_SIZE"))

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

REPO_CLONE_LOCATION = ""

DEFAULT_CONFIGS = {
    "DRILLER_CLASS": "driller.drillers.driller.RepositoryDriller",
    "WORKER_CLASS": "driller.workers.queue_driller_worker.QueueRepositoryNeo4jDrillerWorker"
}

CONFIGS = {**DEFAULT_CONFIGS}



