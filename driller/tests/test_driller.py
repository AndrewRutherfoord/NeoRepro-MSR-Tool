from datetime import datetime, timedelta
import logging

from driller.drillers.driller import LogStorage, Neo4jStorage, RepositoryDriller

logger = logging.getLogger(__name__)

from unittest import TestCase

now = datetime.now()

# Calculate the date and time two weeks ago
period = now - timedelta(weeks=1000)

from driller.settings.default import NEO4J_HOST, NEO4J_PORT, NEO4J_USER, NEO4J_PASSWORD

# class TestConfigDriller(TestCase):
# def test_commit_drill():
#     storage = LogStorage()

#     driller = RepositoryDriller("repos/pydriller", storage)

#     driller.drill_commits(since=period)
#     assert False

def test_commit_drill_neo4j_insert():
    
    storage = Neo4jStorage(
        host=NEO4J_HOST,
        port=NEO4J_PORT,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )

    driller = RepositoryDriller("repos/pydriller", storage)

    driller.drill_repository()
    driller.drill_commits(since=period)
    
    storage.close()
