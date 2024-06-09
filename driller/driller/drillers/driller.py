from abc import ABC, abstractmethod
import logging
import queue

from neo4j import GraphDatabase


from driller.driller_config import Neo4jConfig
from pydriller import Repository, Commit

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "neo4j123")

logger = logging.getLogger(__name__)


class RepositoryDataStorage(ABC):
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

class RepositoryNeo4jStorage(RepositoryDataStorage):

    def __init__(
        self,
        user: str = "neo4j",
        password: str = "",
        host: str = "127.0.0.1",
        port: int = 7687,
        batch_size: int = 200,
    ):
        uri = f"bolt://{host}:{port}"
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.batch_size = batch_size
        self.batch = []

        self._create_indexes_and_constraints()

    def close(self):
        self._process_batch()
        self.driver.close()

    def _create_indexes_and_constraints(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (b:Branch) REQUIRE b.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Developer) REQUIRE d.email IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE")

    def _add_to_batch(self, query, parameters):
        self.batch.append((query, parameters))
        if len(self.batch) >= self.batch_size:
            self._process_batch()

    def _process_batch(self):
        logger.info("Processing Batch")
        if self.batch:
            with self.driver.session() as session:
                with session.begin_transaction() as tx:
                    for operation in self.batch:
                        tx.run(*operation)
            self.batch = []

    def store_repository(self, repo_name):
        self._add_to_batch("MERGE (r:Repository {name: $name})", {"name": repo_name})

    def store_branch(self, repo_name, branch_name):
        self._add_to_batch(
            "MATCH (r:Repository {name: $repo_name}) "
            "MERGE (b:Branch {name: $branch_name})-[:PART_OF]->(r)",
            {
                "repo_name": repo_name,
                "branch_name": branch_name,
            },
        )

    def store_developer(self, author):
        # Store the developer information
        self._add_to_batch(
            "MERGE (d:Developer {email: $email}) " "SET d.name = $name",
            {
                "email": author.email,
                "name": author.name,
            },
        )

    def store_commit(self, repo_name, commit: Commit):
        with self.driver.session() as session:
            self.store_developer(commit.author)

            self._add_to_batch(
                "MATCH (d:Developer {email: $email})  "
                "MERGE (c)-[:AUTHOR]->(d) "
                "SET c.message = $message, c.author = $author, c.date = $date,"
                "c.dmm_unit_size = $dmm_unit_size, c.dmm_unit_complexity = $dmm_unit_complexity, "
                "c.dmm_unit_interfacing = $dmm_unit_interfacing, c.is_merge = $merge",
                {
                    "email": commit.author.email,
                    "message": commit.msg,
                    "author": commit.author.name,
                    "date": commit.author_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "dmm_unit_size": commit.dmm_unit_size,
                    "dmm_unit_complexity": commit.dmm_unit_complexity,
                    "dmm_unit_interfacing": commit.dmm_unit_interfacing,
                    "merge": commit.merge,
                },
            )

            for branch in commit.branches:
                self.store_branch(repo_name, branch)

                self._add_to_batch(
                    "MATCH (b:Branch {name: $branch_name}), (c:Commit {hash: $hash})"
                    "MERGE (c)-[:IN_BRANCH]->(b)",
                    {
                        "branch_name": branch,
                        "hash": commit.hash,
                    },
                )

                # Link the commit to its parent commits
            for parent_hash in commit.parents:
                self._add_to_batch(
                    "MATCH (c:Commit {hash: $hash}), (p:Commit {hash: $parent_hash}) "
                    "MERGE (c)-[:PARENT]->(p)",
                    {
                        "hash": commit.hash,
                        "parent_hash": parent_hash,
                    },
                )


class LogRepositoryStorage(RepositoryDataStorage):

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
    
    

    def __init__(self, repository_path, storage: RepositoryDataStorage):
        self.repository_path = repository_path
        self.repository_name = self.repository_path.split("/")[-1]
        self.storage = storage

    def get_commits(self, pydriller_filters = {}):
        return Repository(self.repository_path, **pydriller_filters).traverse_commits()

    def drill_commits(self, filter_configs : dict = {}, pydriller_filters = {}):
        for commit in self.get_commits(pydriller_filters):
            if self.commit_filter(commit, filter_configs):
                self.storage.store_commit(self.repository_name, commit)
            
    def commit_filter(self, commit, filter_configs : list[dict]) -> bool:
        """Used to determine whether a commit should be inserted into the database

        Args:
            commit (Commit): PyDriller Commit instance.

        Returns:
            bool: whether it should be inserted. If True, commit inserted into storage.
        """
        
        for item in filter_configs:
            field = item.get("field")
            filter_value = item.get("value")
            method = item.get("method", "exact")
            
            if method == "exact" and getattr(commit, field, f"`{field}` not in Commit.") != filter_value:
                return False
            elif method == "!exact" and getattr(commit, field, f"`{field}` not in Commit.") == filter_value:
                return False
            elif method == "contains" and filter_value not in getattr(commit, field, f"`{field}` not in Commit."):
                return False
            elif method == "!contains" and filter_value in getattr(commit, field, f"`{field}` not in Commit."):
                return False
        return True
            

    def drill_repository(self):
        self.storage.store_repository(self.repository_name)
