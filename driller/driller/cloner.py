import os
from git import GitCommandError, InvalidGitRepositoryError, Repo

import logging

def clone_repository(repository_url, repository_location):
    """Clones a Git Repository to a specified local directory.

    Args:
        repository_url (str): http url for a git repository
        repository_location (str): location where the repository should be cloned to
        
    Throws:
        `GitCommandError` when git clone fails
        `InvalidGitRepositoryError` if directory already exists and isn't a git repository.
    """

    if os.path.exists(repository_location):
        try:
            repo = Repo(repository_location)
            if repo.remotes.origin.url == repository_url:
                logging.info(f"Repo `{repository_url}` already cloned.")
                return # Repository already cloned
            else:
                return # Another repo at location
        except InvalidGitRepositoryError as e:
            logging.error(f"Directory `{repository_location}` already exists but isn't a Git Repo.")
            raise e  # Directory exists but not a Git repo.
        

    Repo.clone_from(repository_url, repository_location)
