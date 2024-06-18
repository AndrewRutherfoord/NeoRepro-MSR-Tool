

from enum import Enum
from pydantic import BaseModel


class PydrillerConfig(BaseModel):
    since: str = None
    from_commit: str = None
    from_tag: str = None
    to: str = None
    to_commit: str = None
    to_tag: str = None
    only_in_branch: str = None
    only_no_merge: bool = None
    only_authors: list[str] = None
    only_commits: list[str] = None
    only_release: bool = None
    filepath: str = None
    only_modifications_with_file_types: list[str] = None


class FilterMethod(str, Enum):
    exact = "exact"
    not_exact = "!exact"
    contains = "contains"
    not_contains = "!contains"


class Filter(BaseModel):
    field: str
    value: str
    method: FilterMethod = FilterMethod.contains

    class Config:
        use_enum_values = True


class FiltersConfig(BaseModel):
    commit: list[Filter] = None


class DefaultsConfig(BaseModel):
    delete_clone: bool = False
    index_file_modifications: bool = False
    index_file_diff: bool = False
    pydriller: PydrillerConfig = None
    filters: FiltersConfig = None


class RepositoryConfig(DefaultsConfig):
    name: str
    url: str = None

    # Have to set to None because to make it optional
    delete_clone: bool = None
    index_file_modifications: bool = None
    index_file_diff: bool = None


class DrillConfig(BaseModel):
    defaults: DefaultsConfig
    repositories: list[RepositoryConfig]
    
