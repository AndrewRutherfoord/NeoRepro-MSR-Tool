#!/usr/bin/env python3

from dataclasses import asdict, dataclass
from datetime import datetime
import functools
import logging
import sys
import os

import yaml

from driller.config_driller import (
    Neo4jConfig,
    ProjectConfig,
    ProjectDefaults,
    drill_repositories,
)

sys.path.append(os.path.join(os.path.dirname(__file__), "GraphRepo"))


def parse_config(path):
    with open(path, "r") as ymlfile:
        conf = yaml.load(ymlfile, Loader=yaml.FullLoader)

        neo = Neo4jConfig(**conf.get("neo"))

        defaults = ProjectDefaults(**conf.get("repositories").get("defaults"))

        projects = []
        for repo in conf.get("repositories").get("projects"):
            projects.append(ProjectConfig(**repo))

        return neo, defaults, projects


def main():
    # neo = Neo4jConfig(
    #     db_url="localhost",
    #     db_user="neo4j",
    #     db_pwd="neo4j123",
    # )
    # project = ProjectConfig(repo="../repos/vee-validate/", project_id="vee-validate")

    # defaults = ProjectDefaults(
    #     index_code=False,
    #     index_developer_email=True,
    # )
    # return
    neo, defaults, projects = parse_config("driller/configs/test.yaml")
    drill_repositories(neo=neo, projects=projects, project_defaults=defaults)


if __name__ == "__main__":
    main()
