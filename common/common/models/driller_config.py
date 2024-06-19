from enum import Enum
from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
    field_serializer,
    ConfigDict,
)
from typing import List, Optional
from datetime import datetime


class PydrillerConfig(BaseModel):
    since: Optional[datetime] = None
    to: Optional[datetime] = None
    from_commit: Optional[str] = None
    to_commit: Optional[str] = None
    from_tag: Optional[str] = None
    to_tag: Optional[str] = None
    only_in_branch: Optional[str] = None
    only_no_merge: Optional[bool] = None
    only_authors: Optional[list[str]] = None
    only_commits: Optional[list[str]] = None
    only_release: Optional[bool] = None
    filepath: Optional[str] = None
    only_modifications_with_file_types: Optional[list[str]] = None

    @field_validator("since", "to")
    def parse_dates(cls, value):
        """Parses datetime strings of the format YYYY-MM-DD."""

        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d")
        return value

    @field_serializer("since", "to")
    def serialize_dt(self, dt: datetime, _info):
        """Converts the datetime object to a string in the format of YYYY-MM-DD."""
        if dt is None:
            return None
        return dt.strftime("%Y-%m-%d")

    def apply_defaults(self, defaults):
        for attr in vars(defaults):
            if getattr(self, attr) is None:
                setattr(self, attr, getattr(defaults, attr))


class FilterMethod(str, Enum):
    exact = "exact"
    not_exact = "!exact"
    contains = "contains"
    not_contains = "!contains"


class Filter(BaseModel):
    field: str
    value: str
    method: FilterMethod = FilterMethod.contains

    model_config = {"use_enum_values": True}


class FiltersConfig(BaseModel):
    commit: list[Filter] = None

    def apply_defaults(self, defaults):
        if self.commit is None:
            self.commit = defaults.commit
        else:
            self.commit.apply_defaults(defaults.commit)


class DefaultsConfig(BaseModel):
    delete_clone: bool = False
    index_file_modifications: bool = False
    index_file_diff: bool = False
    pydriller: Optional[PydrillerConfig] = None
    filters: Optional[FiltersConfig] = None


class RepositoryConfig(DefaultsConfig):
    name: str
    url: Optional[str] = None

    # Have to set to None because to make it optional
    delete_clone: Optional[bool] = None
    index_file_modifications: Optional[bool] = None
    index_file_diff: Optional[bool] = None

    def apply_defaults(self, defaults: DefaultsConfig):
        """Applies the defaults to the repository config. If value is set to None, it will be set to the default value (if one exists).

        Args:
            defaults (DefaultsConfig): The defaults to apply.
        """
        if self.delete_clone is None:
            self.delete_clone = defaults.delete_clone
        if self.index_file_modifications is None:
            self.index_file_modifications = defaults.index_file_modifications
        if self.index_file_diff is None:
            self.index_file_diff = defaults.index_file_diff

        if self.pydriller is None:
            self.pydriller = defaults.pydriller
        else:
            self.pydriller.apply_defaults(defaults.pydriller)

        if self.filters is None:
            self.filters = defaults.filters
        else:
            self.filters.apply_defaults(defaults.filters)


class DrillConfig(BaseModel):
    defaults: DefaultsConfig
    repositories: list[RepositoryConfig]


class SingleDrillConfig(BaseModel):
    defaults: Optional[DefaultsConfig] = None
    repository: RepositoryConfig

    job_id: Optional[int] = None

    def apply_defaults(self):
        """Applies the defaults to the repository config.

        Returns:
            RepositoryConfig: The repository config with the defaults applied. (Also store in self.repository)
        """
        if self.defaults is None:
            self.repository.apply_defaults(self.defaults)
        return self.repository
