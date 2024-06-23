import logging
import os

# DATE_FORMAT = "%d %B, %Y %H:%M"
DATE_FORMAT = "%Y-%m-%d"

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD")

NEO4J_USER = os.environ.get("NEO4J_USER", None)
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", None)
NEO4J_HOST = os.environ.get("NEO4J_HOST", None)
NEO4J_PORT = os.environ.get("NEO4J_PORT", None)

NEO4J_DEFAULT_BATCH_SIZE = None
try:
    NEO4J_DEFAULT_BATCH_SIZE = int(os.environ.get("NEO4J_DEFAULT_BATCH_SIZE"))
except ValueError:
    raise ValueError("NEO4J_DEFAULT_BATCH_SIZE must be an integer.")

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

REPO_CLONE_LOCATION = os.environ.get("REPO_CLONE_LOCATION", "/tmp/repos")

DEFAULT_CONFIGS = {
    "REPOSITORY_STORAGE_CLASS": "driller.drillers.storage.RepositoryNeo4jStorage",
    "REPOSITORY_DRILLER_CLASS": "driller.drillers.driller.RepositoryDriller",
    "WORKER_CLASS": "driller.workers.queue_driller_worker.QueueRepositoryNeo4jDrillerWorker",
}

CONFIGS = {**DEFAULT_CONFIGS}
