from datetime import datetime, timedelta
import logging

from driller.drillers.driller import (
    RepositoryDataStorage,
    LogRepositoryStorage,
    RepositoryNeo4jStorage,
    RepositoryDriller,
)
from pydriller import Commit

logger = logging.getLogger(__name__)

now = datetime.now()

# Calculate the date and time two weeks ago
period = now - timedelta(weeks=52)

from driller.settings.default import NEO4J_HOST, NEO4J_PORT, NEO4J_USER, NEO4J_PASSWORD

# class TestConfigDriller(TestCase):
# def test_commit_drill():
#     storage = LogRepositoryStorage()

#     driller = RepositoryDriller("repos/pydriller", storage)

#     driller.drill_commits(since=period)
#     assert False


def test_commit_drill_neo4j_insert():
    storage = RepositoryNeo4jStorage(
        host=NEO4J_HOST,
        port=NEO4J_PORT,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )

    driller = RepositoryDriller("repos/pydriller", storage)

    driller.drill_repository()
    driller.drill_commits(pydriller_filters={"since": period})

    storage.close()


class TestStorage(RepositoryDataStorage):
    def store_repository(self, repo_name):
        assert repo_name == "pydriller"

    def store_branch(self, repo_name, branch_name):
        pass

    def store_commit(self, repo_name, commit):
        pass
    
    def store_developer(self, developer):
        pass


def test_commit_exact_filter():
    msg = "Update continuous-integration-workflow.yml"

    class TestCaseStorage(TestStorage):
        def store_commit(self, repo_name, commit: Commit):
            assert commit.msg == msg
            logger.info(commit.msg)

    storage = TestCaseStorage()

    driller = RepositoryDriller("repos/pydriller", storage)

    driller.drill_repository()
    driller.drill_commits(
        pydriller_filters={"since": period},
        filter_configs=[
            {
                "field": "msg",
                "value": msg,
                "method": "exact",
            }
        ],
    )


def test_commit_contains_filter():
    check_str = "Update"

    class TestCaseStorage(TestStorage):
        def store_commit(self, repo_name, commit: Commit):
            assert check_str in commit.msg
            logger.info(commit.msg)

    storage = TestCaseStorage()

    driller = RepositoryDriller("repos/pydriller", storage)

    driller.drill_repository()
    driller.drill_commits(
        pydriller_filters={"since": period},
        filter_configs=[
            {
                "field": "msg",
                "value": check_str,
                "method": "contains",
            }
        ],
    )


def test_commit_contains_filter():
    check_str = "Update"

    class TestCaseStorage(TestStorage):
        def store_commit(self, repo_name, commit: Commit):
            assert check_str in commit.msg
            logger.info(commit.msg)

    storage = TestCaseStorage()

    driller = RepositoryDriller("repos/pydriller", storage)

    driller.drill_repository()
    driller.drill_commits(
        pydriller_filters={"since": period},
        filter_configs=[
            {
                "field": "msg",
                "value": check_str,
                "method": "contains",
            }
        ],
    )
