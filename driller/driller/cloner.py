import logging
import os
from git import GitCommandError, InvalidGitRepositoryError, Repo

logger = logging.getLogger(__name__)


def clone_repository(repository_url, repository_location):
    """Clones a Git Repository to a specified local directory.

    Args:
        repository_url (str): http url for a git repository
        repository_location (str): location where the repository should be cloned to

    Throws:
        `GitCommandError` when git clone fails
        `InvalidGitRepositoryError` if directory already exists and isn't a git repository.
    """

    try:
        if os.path.exists(repository_location):
            repo = Repo(repository_location)
            if repo.remotes.origin.url == repository_url:
                logger.info(f"Repo `{repository_url}` already cloned.")
                return  # Repository already cloned
            else:
                return  # Another repo at location
        Repo.clone_from(repository_url, repository_location)

    except GitCommandError:
        logger.error(
            "Could not get Git Repository. Probably because it no longer exists."
        )
        raise LookupError("Repository not found on remote host.")
    except InvalidGitRepositoryError as e:
        logger.error(
            f"Directory `{repository_location}` already exists but isn't a Git Repo."
        )
        raise e  # Directory exists but not a Git repo.
    except Exception as e:
        logger.exception(e)
        raise e


def remove_repository_clone(repository_location):
    """Deletes a folder from a given path. Intended to be used with repositories, but is just deleting a folder."""
    try:
        if os.path.exists(repository_location):
            os.remove(repository_location)
    except Exception as e:
        logger.exception(e)
        raise e
