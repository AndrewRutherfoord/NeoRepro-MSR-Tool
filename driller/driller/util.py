import yaml
import importlib
import logging
from datetime import datetime, timedelta

from driller.settings.default import DATE_FORMAT

logger = logging.getLogger(__name__)


def get_class(class_path):

    # Split the path to get the module and class name
    module_path, class_name = class_path.rsplit(".", 1)

    # Import the module
    module = importlib.import_module(module_path)

    # Get the class
    return getattr(module, class_name)


def remove_none_values(d):
    if not isinstance(d, dict):
        return d
    return {k: remove_none_values(v) for k, v in d.items() if v is not None}


def load_yaml(path):
    with open(path, "r") as ymlfile:
        content = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return content


def handle_date(
    data: dict, date_key: str, boundary: datetime = None
) -> datetime | None:
    """Handles the date that is passed in from the configuration file.
    If the given date key provided, then set it to boundary. Suggests user wants all commits to be mined.
    If given key not provided, set to none.

    Args:
        data (dict): dictionary which may contain a data.
        date_key (str): key for date attribute in `data`
        boundary (datetime, optional): A datatime object to set the date field to if key present but is None. Defaults to None.

    Returns:
        datetime: The datatime object
    """
    if date_key in data:
        return (
            datetime.strptime(data[date_key], DATE_FORMAT)
            if data[date_key]
            else boundary
        )
    return None


# def parse_config(conf):
#     logger.info(conf)
#     neo = None
#     try:
#         neo = Neo4jConfig(**conf["neo"])
#     except KeyError as e:
#         logger.error("Key error. Missing key `neo` configuration.")
#
#     try:
#         defaults_dict = conf["repositories"]["defaults"]
#         defaults_dict["start_date"] = handle_date(
#             defaults_dict, "start_date", datetime(1, 1, 1)
#         )
#         defaults_dict["end_date"] = handle_date(defaults_dict, "end_date", datetime.now())
#     except KeyError as e:
#         logger.error(f"Key error. Missing key `{e}` configuration.")
#
#     defaults = ProjectDefaults(**defaults_dict)
#
#     projects = []
#     for repo in conf.get("repositories").get("projects"):
#         repo["start_date"] = handle_date(repo, "start_date", datetime(1, 1, 1))
#
#         # Added 24 hours just to cancel our any timezone issues.
#         repo["end_date"] = handle_date(
#             repo, "end_date", datetime.now() + timedelta(hours=24)
#         )
#         projects.append(ProjectConfig(**repo))
#
#     return neo, defaults, projects

