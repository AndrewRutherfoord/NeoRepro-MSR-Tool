import logging

from pydriller import Repository, Commit

from driller.drillers.storage import RepositoryDataStorage
from driller.util import handle_date

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "neo4j123")

logger = logging.getLogger(__name__)


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
            self.storage.store_modified_file(commit, file, self.repository_name)

    def drill_commits(self, filters: dict = {}, pydriller_filters={}, index_file_modifications=True):
        """Drills all the commits based on the filters and pydriller configs.
        Inserts all the data into the storage.
        Args:
            filters (dict, optional): Filters to apply to the commits. Defaults to {}.
            pydriller_filters (dict, optional): Pydriller configurations. Defaults to {}.
            index_file_modifications (bool, optional): Whether to index file modifications. Defaults to True.
        """
        
        pydriller_filters = {} if pydriller_filters is None else pydriller_filters
        
        # Handle the conversion of date stings to datetime objects
        pydriller_filters["since"] = handle_date(pydriller_filters,"since")
        pydriller_filters["to"] = handle_date(pydriller_filters,"to")

        for commit in self.get_commits(pydriller_filters):
            if self.commit_filter(commit, filters):
                self._handle_branches(commit.branches)
                self._handle_committer(commit.author)

                self.storage.store_commit(self.repository_name, commit)

                if index_file_modifications:
                    self._handle_modified_files(commit, commit.modified_files)

    def commit_filter(self, commit, filter_configs: list[dict] = {}) -> bool:
        """Used to determine whether a commit should be inserted into the database

        Args:
            commit (Commit): PyDriller Commit instance.

        Returns:
            bool: whether it should be indexed. If True, commit inserted into storage.
        """

        if filter_configs is None:
            # If no filters given, then automatically accept.
            return True
        
        for item in filter_configs.get("commit", []):
            field = item.get("field")
            filter_value = item.get("value")
            method = item.get("method", "exact")

            value = getattr(commit, field, f"`{field}` not in Commit.")

            # TODO: This can probably be done in a nicer way.
            # TODO: Regex support??
            if isinstance(filter_value, list):
                if method == "exact" and not any(fv == value for fv in filter_value):
                    return False
                elif method == "!exact" and any(fv == value for fv in filter_value):
                    return False
                elif method == "contains" and not any(
                    fv in value for fv in filter_value
                ):
                    return False
                elif method == "!contains" and any(fv in value for fv in filter_value):
                    return False
            else:
                if method == "exact" and value != filter_value:
                    return False
                elif method == "!exact" and value == filter_value:
                    return False
                elif method == "contains" and filter_value not in value:
                    return False
                elif method == "!contains" and filter_value in value:
                    return False

        return True

    def drill_repository(self):
        """Drills the repository information and inserts it into the storage."""
        self.storage.store_repository(self.repository_name)
