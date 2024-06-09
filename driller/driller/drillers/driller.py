from abc import ABC, abstractmethod
import logging
import queue

from neo4j import GraphDatabase


from driller.driller_config import Neo4jConfig
from pydriller import Repository, Commit

from repos.pydriller.pydriller.domain.commit import ModificationType

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

    @abstractmethod
    def store_developer(self, developer):
        pass

    @abstractmethod
    def store_modified_file(self, commit, file):
        pass


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
        """
        Closes the Neo4j connection.
        Processes remaining batch just before close.
        """
        self._process_batch()
        self.driver.close()

    def _create_indexes_and_constraints(self):
        """ Creates the uniqueness constraints for the repository database."""
        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.name IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Branch) REQUIRE (b.name, b.repository) IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Developer) REQUIRE d.email IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE"
            )

    def _add_to_batch(self, query, parameters):
        """Adds a query to the batch of queries.

        Args:
            query (str): query string
            parameters (dict): the parameters that will be inserted into the queries.
        """
        self.batch.append((query, parameters))
        if len(self.batch) >= self.batch_size:
            self._process_batch()

    def _process_batch(self):
        """Runs a batch of cypher commands on the Neo4j DB."""
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
            "MERGE (b:Branch {name: $branch_name, repository: $repo_name })-[:PART_OF]->(r)",
            {
                "repo_name": repo_name,
                "branch_name": branch_name,
            },
        )

    def store_developer(self, developer):
        """Store the information for a developer."""

        self._add_to_batch(
            "MERGE (d:Developer {email: $email}) SET d.name = $name",
            {
                "email": developer.email,
                "name": developer.name,
            },
        )

    def store_commit(self, repo_name, commit: Commit):
        """Stores an instance of a commit and links it to the author."""

        # Create or Update commit and link it to the developer as an `AUTHOR` relationship.
        self._add_to_batch(
            "MATCH (d:Developer {email: $email}) "
            "MERGE (c:Commit {hash: $hash}) "
            "MERGE (c)-[:AUTHOR]->(d) "
            "SET c.message = $message, c.author = $author, c.date = $date,"
            "c.dmm_unit_size = $dmm_unit_size, c.dmm_unit_complexity = $dmm_unit_complexity, "
            "c.dmm_unit_interfacing = $dmm_unit_interfacing, c.is_merge = $merge",
            {
                "hash": commit.hash,
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

        for parent_hash in commit.parents:
            # Create a `PARENT` relationship between the current commit and it's parents
            self._add_to_batch(
                "MATCH (c:Commit {hash: $hash}), (p:Commit {hash: $parent_hash}) "
                "MERGE (c)-[:PARENT]->(p)",
                {
                    "hash": commit.hash,
                    "parent_hash": parent_hash,
                },
            )

        for branch in commit.branches:
            # Create an `IN_BRANCH` relationship between the commit and the branches it belongs to.
            self._add_to_batch(
                "MATCH (b:Branch {name: $branch_name}), (c:Commit {hash: $hash})"
                "MERGE (c)-[:IN_BRANCH]->(b)",
                {
                    "branch_name": branch,
                    "hash": commit.hash,
                },
            )

    def store_modified_file(self, commit, file):
        # Creates or Updates a FIle instance and links it to the commit with a `MODIFIED` relationship
        # Relationship holds all the modification information
        self._add_to_batch(
            "MATCH (c:Commit {hash: $hash}) "
            "MERGE (f:File {name: $filename}) "
            "MERGE (c)-[r:MODIFIED]->(f) "
            "SET f.name = $filename, "
            "r.old_path = $old_path, r.new_path = $new_path, "
            "r.filename = $filename, r.change_type = $change_type, "
            "r.added_lines = $added_lines, r.deleted_lines = $deleted_lines, "
            "r.nloc = $nloc, r.complexity = $complexity, r.token_count = $token_count",
            {
                "hash": commit.hash,
                "filename": file.filename,
                "old_path": file.old_path,
                "new_path": file.new_path,
                "filename": file.filename,
                "change_type": file.change_type.name,  # ENUM
                "added_lines": file.added_lines,
                "deleted_lines": file.deleted_lines,
                "nloc": file.nloc,
                "complexity": file.complexity,
                "token_count": file.token_count,
            },
        )
        # TODO: Other fields that can be used: diff, diff_parsed, source_code, source_code_before, methods, methods_before, changed_methods,

        # If the file change is a RENAME, create a `RENAMED_TO` relation from the old file node.
        if file.change_type.name == "RENAME":
            old_name = file.old_path.split("/")[-1]
            logger.info(old_name)
            self._add_to_batch(
                "MATCH  (old:File {name : $old_name}),(new:File {name: $filename})"
                "MERGE (old)-[:RENAMED_TO]->(new)",
                {"old_name": old_name, "filename": file.filename},
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

    def get_commits(self, pydriller_filters={}):
        return Repository(self.repository_path, **pydriller_filters).traverse_commits()

    def _handle_branches(self, branch_names):
        for b in branch_names:
            self.storage.store_branch(self.repository_name, b)

    def _handle_committer(self, committer):
        self.storage.store_developer(committer)

    def _handle_modified_files(self, commit: Commit, files):
        for file in files:
            self.storage.store_modified_file(commit, file)

    def drill_commits(self, filters: dict = {}, pydriller_filters={}, drill_files=True):
        """Drills all the commits based on the filters and pydriller configs.
        Inserts all the data into the storage.
        """
        for commit in self.get_commits(pydriller_filters):
            if self.commit_filter(commit, filters):
                logger.info("Drilling Commit")
                self._handle_branches(commit.branches)
                self._handle_committer(commit.author)

                self.storage.store_commit(self.repository_name, commit)

                if drill_files:
                    self._handle_modified_files(commit, commit.modified_files)

    def commit_filter(self, commit, filter_configs: list[dict]) -> bool:
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

            if (
                method == "exact"
                and getattr(commit, field, f"`{field}` not in Commit.") != filter_value
            ):
                return False
            elif (
                method == "!exact"
                and getattr(commit, field, f"`{field}` not in Commit.") == filter_value
            ):
                return False
            elif method == "contains" and filter_value not in getattr(
                commit, field, f"`{field}` not in Commit."
            ):
                return False
            elif method == "!contains" and filter_value in getattr(
                commit, field, f"`{field}` not in Commit."
            ):
                return False
        return True

    def drill_repository(self):
        """Drills the repository information and inserts it into the storage."""
        self.storage.store_repository(self.repository_name)
