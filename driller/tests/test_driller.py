from datetime import datetime, timedelta
import logging

from driller.drillers.driller import (
    RepositoryDataStorage,
    RepositoryDriller,
)
from driller.drillers.storage import LogRepositoryStorage, RepositoryNeo4jStorage
from pydriller import Commit

logger = logging.getLogger(__name__)

now = datetime.now()

period = datetime(2023, 1, 1)

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

    def store_modified_file(self, commit, file, repository_name):
        pass


def test_commit_exact_filter():
    msg = "Update continuous-integration-workflow.yml"

    class TestCaseStorage(TestStorage):
        def store_commit(self, repo_name, commit: Commit):
            assert commit.msg == msg
            logger.info(commit.msg)

    driller = RepositoryDriller("repos/pydriller", TestCaseStorage())

    driller.drill_repository()
    driller.drill_commits(
        pydriller_filters={"since": period},
        filters=[
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

    driller = RepositoryDriller("repos/pydriller", TestCaseStorage())

    driller.drill_repository()
    driller.drill_commits(
        drill_files=False,
        pydriller_filters={"since": period},
        filters=[
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

    driller = RepositoryDriller("repos/pydriller", TestCaseStorage())

    driller.drill_repository()
    driller.drill_commits(
        drill_files=False,
        pydriller_filters={"since": period},
        filters=[
            {
                "field": "msg",
                "value": check_str,
                "method": "contains",
            }
        ],
    )


# Tests the OR functionality with commit filters
def test_commit_contains_list_filter():
    check_strs = ["Update", "docs"]

    class TestCaseStorage(TestStorage):
        def store_commit(self, repo_name, commit: Commit):
            logger.info(commit.msg)
            assert any(s in commit.msg for s in check_strs)

    driller = RepositoryDriller("repos/pydriller", TestCaseStorage())

    driller.drill_repository()
    driller.drill_commits(
        drill_files=False,
        pydriller_filters={"since": period},
        filters=[
            {
                "field": "msg",
                "value": check_strs,
                "method": "contains",
            }
        ],
    )


# Tests the AND functionality with commit filters
def test_commit_contains_filter_AND():
    check_strs = ["Update", "docs"]

    class TestCaseStorage(TestStorage):
        def store_commit(self, repo_name, commit: Commit):
            logger.info(commit.msg)
            assert all(s in commit.msg for s in check_strs)

    driller = RepositoryDriller("repos/pydriller", TestCaseStorage())

    driller.drill_repository()
    driller.drill_commits(
        drill_files=False,
        pydriller_filters={"since": period},
        filters=[
            {
                "field": "msg",
                "value": check_strs[0],
                "method": "contains",
            },
            {
                "field": "msg",
                "value": check_strs[1],
                "method": "contains",
            },
        ],
    )
