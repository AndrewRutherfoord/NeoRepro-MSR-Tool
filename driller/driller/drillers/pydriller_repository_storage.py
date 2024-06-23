from abc import ABC, abstractmethod
from pydriller import Commit
from pydriller.domain.commit import Developer, ModifiedFile

import logging

logger = logging.getLogger(__name__)


class RepositoryDataStorage(ABC):
    @abstractmethod
    def store_repository(self, repo_name: str):
        pass

    @abstractmethod
    def store_branch(self, repo_name: str, branch_name: str):
        pass

    @abstractmethod
    def store_commit(self, repo_name: str, commit: Commit):
        pass

    @abstractmethod
    def store_developer(self, developer: Developer):
        pass

    @abstractmethod
    def store_modified_file(
        self, commit: Commit, file: ModifiedFile, repository_name: str, index_diff=False
    ):
        pass


class LogRepositoryStorage(RepositoryDataStorage):
    """An example Repository storage which logs the data to the console.
    Just for testing purposes.
    """

    def __init__(self):
        pass

    def store_commit(self, repo_name: str, commit: Commit):
        logger.info(
            {
                "repository_name": repo_name,
                "hash": commit.hash,
                "message": commit.msg,
                "author": commit.author.name,
                "date": commit.author_date.strftime("%Y-%m-%d %H:%M:%S"),
                "parents": commit.parents,
                "dmm_unit_size": commit.dmm_unit_size,
                "dmm_unit_complexity": commit.dmm_unit_complexity,
                "dmm_unit_interfacing": commit.dmm_unit_interfacing,
                "merge": commit.merge,
            }
        )

    def store_repository(self, repo_name):
        logger.info(repo_name)

    def store_branch(self, repo_name, branch_name):
        logger.info(f"Branch {branch_name} from {repo_name}.")
