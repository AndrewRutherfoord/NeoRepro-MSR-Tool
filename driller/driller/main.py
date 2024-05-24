#!/usr/bin/env python3

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import functools
import logging
import sys
import os

import yaml

from driller.cloner import clone_repository
from driller.config_driller import (
    Neo4jConfig,
    ProjectConfig,
    ProjectDefaults,
    drill_repositories,
)
from driller.util import load_yaml, parse_config

def main():
    conf = load_yaml("driller/configs/test.yaml")
    neo, defaults, projects = parse_config(conf)
    drill_repositories(neo=neo, projects=projects, project_defaults=defaults)


if __name__ == "__main__":
    main()
