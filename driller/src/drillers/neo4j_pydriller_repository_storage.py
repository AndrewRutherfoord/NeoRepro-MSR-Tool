import hashlib
import logging

from pydriller import Commit
from pydriller.domain.commit import Developer, ModifiedFile

from src.drillers.neo4j_storage import Neo4jStorage
from src.drillers.pydriller_repository_storage import RepositoryDataStorage

logger = logging.getLogger(__name__)


class RepositoryNeo4jStorage(Neo4jStorage, RepositoryDataStorage):
    """
    Neo4j storage implemetation that stores data for a PyDriller repository.
    """

    def __init__(
        self,
        user: str = "neo4j",
        password: str = "",
        host: str = "neo4j",
        port: int = 7687,
        batch_size: int = 200,
    ):
        super().__init__(user, password, host, port, batch_size)

        self._create_indexes_and_constraints()

    def _create_indexes_and_constraints(self):
        """Creates the uniqueness constraints for the repository database."""
        with self.driver.session() as session:
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.name IS UNIQUE"
            )
            # session.run(
            #     "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Branch) REQUIRE b.hash IS UNIQUE"
            # )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Developer) REQUIRE d.email IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Commit) REQUIRE c.hash IS UNIQUE"
            )

    def store_repository(self, repo_name):
        """Creates a `Repository` node

        Args:
            repo_name: Name of the repository to store.
        """
        self._add_to_batch("MERGE (r:Repository {name: $name})", {"name": repo_name})

    def hash_branch(self, branch_name, repository_name):
        """Hashes the branch name and repository name together to produce a unique identifier for the branch."""

        return hashlib.sha224(
            str(f"{branch_name}:{repository_name}").encode("utf-8")
        ).hexdigest()

    def store_branch(self, repo_name, branch_name):
        """Store a `Branch` node.

        Args:
            repo_name: Name of repository which branch belongs to.
            branch_name: Name of branhc
        """

        self._add_to_batch(
            "MATCH (r:Repository {name: $repo_name}) "
            "MERGE (b:Branch {hash: $branch_hash })-[:PART_OF]->(r)"
            "SET b.repository = $repo_name, b.name = $branch_name",
            {
                "branch_hash": self.hash_branch(branch_name, repo_name),
                "repo_name": repo_name,
                "branch_name": branch_name,
            },
        )

    def store_developer(self, developer: Developer):
        """Store the information for a developer."""

        self._add_to_batch(
            "MERGE (d:Developer {email: $email}) SET d.name = $name",
            {
                "email": developer.email,
                "name": developer.name,
            },
        )

    def store_commit(self, repo_name, commit: Commit):
        """Stores an instance of a commit and links it to the author and it's parent commit."""

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
                "MATCH (c:Commit {hash: $hash}) "
                "MATCH (p:Commit {hash: $parent_hash}) "
                "MERGE (c)-[:PARENT]->(p)",
                {
                    "hash": commit.hash,
                    "parent_hash": parent_hash,
                },
            )

        for branch in commit.branches:
            # Create an `IN_BRANCH` relationship between the commit and the branches it belongs to.
            self._add_to_batch(
                "MATCH (b:Branch {hash: $branch_hash})"
                "MATCH (c:Commit {hash: $commit_hash})"
                "MERGE (c)-[:IN_BRANCH]->(b)",
                {
                    "branch_hash": self.hash_branch(branch, repo_name),
                    "commit_hash": commit.hash,
                },
            )

    def store_modified_file(
        self, commit: Commit, file: ModifiedFile, repository_name: str, index_diff=False
    ):
        """Stores a file modification and links it to the commit.
        If the file change is a RENAME, creates a `RENAMED_TO` relation from the old file node.

        Args:
            commit: Pydriller Commit which the file was modified in.
            file: PyDriller ModifiedFile instance to store.
            repository_name: Used in filename hash.
            index_diff: Whether to index the file git diff. Increases drilling time.
        """

        logger.debug(f"Storing file {file.filename} in commit {commit.hash}")

        # Creates or Updates a FIle instance and links it to the commit with a `MODIFIED` relationship
        # Relationship holds all the modification information
        query_str = """MATCH (c:Commit {hash: $commit_hash}) 
            MERGE (f:File {hash: $file_hash})
            MERGE (c)-[r:MODIFIED]->(f)
            SET f.name = $filename,
            r.old_path = $old_path, r.new_path = $new_path,
            r.filename = $filename, r.change_type = $change_type,
            r.added_lines = $added_lines, r.deleted_lines = $deleted_lines,
            r.nloc = $nloc, r.complexity = $complexity, r.token_count = $token_count"""

        values = {
            "commit_hash": commit.hash,
            "file_hash": hashlib.sha224(
                str(f"{file.filename}:{repository_name}").encode("utf-8")
            ).hexdigest(),
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
        }

        if index_diff:
            query_str += ", r.diff = $diff"
            values["diff"] = file.diff

        self._add_to_batch(
            query_str,
            values,
        )
        # TODO: Other fields that can be used: diff, diff_parsed, source_code, source_code_before, methods, methods_before, changed_methods,

        # If the file change is a RENAME, create a `RENAMED_TO` relation from the old file node.
        if file.change_type.name == "RENAME":
            old_name = file.old_path.split("/")[-1]
            old_file_hash = hashlib.sha224(
                str(f"{old_name}:{repository_name}").encode("utf-8")
            ).hexdigest()
            new_file_hash = hashlib.sha224(
                str(f"{file.filename}:{repository_name}").encode("utf-8")
            ).hexdigest()
            self._add_to_batch(
                "MATCH  (old:File {hash : $old_hash})"
                "MATCH (new:File {hash: $new_hash})"
                "MERGE (old)-[:RENAMED_TO]->(new)",
                {"old_hash": old_file_hash, "new_hash": new_file_hash},
            )
