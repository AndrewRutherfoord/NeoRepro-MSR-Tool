from abc import ABC, abstractmethod
import logging

from neo4j import GraphDatabase


from driller.driller_config import Neo4jConfig
from pydriller import Repository, Commit

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "neo4j123")

logger = logging.getLogger(__name__)


class DataStorage(ABC):
    @abstractmethod
    def store_repository(self, repo_name):
        pass

    @abstractmethod
    def store_branch(self, repo_name, branch_name):
        pass

    @abstractmethod
    def store_commit(self, repo_name, commit: Commit):
        pass

    # @abstractmethod
    # def store_modification(self, commit, modification):
    #     pass


class Neo4jStorage(DataStorage):

    def __init__(
        self,
        user: str = "neo4j",
        password: str = "",
        host: str = "127.0.0.1",
        port: int = 7687,
    ):
        uri = f"bolt://{host}:{port}"
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def store_repository(self, repo_name):
        with self.driver.session() as session:
            session.run("MERGE (r:Repository {name: $name})", name=repo_name)

    def store_branch(self, repo_name, branch_name):
        with self.driver.session() as session:
            session.run(
                "MATCH (r:Repository {name: $repo_name}) "
                "MERGE (b:Branch {name: $branch_name})-[:PART_OF]->(r)",
                repo_name=repo_name,
                branch_name=branch_name,
            )

    def store_developer(self, author):
        with self.driver.session() as session:
            # Store the developer information
            session.run(
                "MERGE (d:Developer {email: $email}) " "SET d.name = $name",
                email=author.email,
                name=author.name,
            )

    def store_commit(self, repo_name, commit: Commit):
        with self.driver.session() as session:
            self.store_developer(commit.author)

            session.run(
                "MATCH (d:Developer {email: $email})  "
                "MERGE (c)-[:AUTHOR]->(d) "
                "SET c.message = $message, c.author = $author, c.date = $date,"
                "c.dmm_unit_size = $dmm_unit_size, c.dmm_unit_complexity = $dmm_unit_complexity, "
                "c.dmm_unit_interfacing = $dmm_unit_interfacing, c.is_merge = $merge",
                email=commit.author.email,
                message=commit.msg,
                author=commit.author.name,
                date=commit.author_date.strftime("%Y-%m-%d %H:%M:%S"),
                dmm_unit_size=commit.dmm_unit_size,
                dmm_unit_complexity=commit.dmm_unit_complexity,
                dmm_unit_interfacing=commit.dmm_unit_interfacing,
                merge=commit.merge,
            )

            for branch in commit.branches:
                self.store_branch(repo_name, branch)

                session.run(
                    "MATCH (b:Branch {name: $branch_name}), (c:Commit {hash: $hash})"
                    "MERGE (c)-[:IN_BRANCH]->(b)",
                    branch_name=branch,
                    hash=commit.hash,
                )

                # Link the commit to its parent commits
            for parent_hash in commit.parents:
                session.run(
                    "MATCH (c:Commit {hash: $hash}), (p:Commit {hash: $parent_hash}) "
                    "MERGE (c)-[:PARENT]->(p)",
                    hash=commit.hash,
                    parent_hash=parent_hash,
                )


class LogStorage(DataStorage):

    def __init__(self):
        pass

    def store_commit(self, repo_name, commit: Commit):
        logger.info(
            {
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
        pass


class RepositoryDriller:
    """A GraphRepo Driller that takes configs from config objects."""

    def __init__(self, repository_path, storage: DataStorage):
        self.repository_path = repository_path
        self.repository_name = self.repository_path.split("/")[-1]
        self.storage = storage

    def get_commits(self, **kwargs):
        return Repository(self.repository_path, **kwargs).traverse_commits()

    def drill_commits(self, **kwargs):
        for commit in self.get_commits(**kwargs):
            self.storage.store_commit(self.repository_name, commit)

    def drill_repository(self):
        self.storage.store_repository(self.repository_name)
