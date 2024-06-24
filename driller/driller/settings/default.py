import logging
import os

LOG_LEVEL = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO"))
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# DATE_FORMAT = "%d %B, %Y %H:%M"
DATE_FORMAT = "%Y-%m-%d"

RABBITMQ_LOG_LEVEL = os.environ.get("RABBITMQ_LOG_LEVEL", LOG_LEVEL)
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT")
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD")

NEO4J_LOG_LEVEL = os.environ.get("NEO4J_LOG_LEVEL", LOG_LEVEL)
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", None)
NEO4J_HOST = os.environ.get("NEO4J_HOST", "neo4j")
NEO4J_PORT = os.environ.get("NEO4J_PORT")

NEO4J_DEFAULT_BATCH_SIZE = None
try:
    NEO4J_DEFAULT_BATCH_SIZE = int(os.environ.get("NEO4J_DEFAULT_BATCH_SIZE", 50))
except ValueError:
    raise ValueError("NEO4J_DEFAULT_BATCH_SIZE must be an integer.")


REPO_CLONE_LOCATION = os.environ.get("REPO_CLONE_LOCATION", "/tmp/repos")

DEFAULT_CONFIGS = {
    "REPOSITORY_STORAGE_CLASS": "driller.drillers.neo4j_pydriller_repository_storage.RepositoryNeo4jStorage",
    "REPOSITORY_DRILLER_CLASS": "driller.drillers.driller.RepositoryDriller",
    "WORKER_CLASS": "driller.workers.queue_driller_worker.QueueRepositoryNeo4jDrillerWorker",
}

CONFIGS = {**DEFAULT_CONFIGS}
