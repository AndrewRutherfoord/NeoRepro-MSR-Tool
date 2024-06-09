import pytest
import yaml
import jsonschema
import json


def get_schema():
    with open("./schemas/schema.json", "r") as f:
        return json.load(f)


def test_empty():
    schema = get_schema()
    with pytest.raises(jsonschema.exceptions.ValidationError):
        # Expect Failure
        jsonschema.validate(instance={}, schema=schema)


def test_minimum():
    schema = get_schema()

    data = {"defaults": {}, "repositories": []}

    jsonschema.validate(instance=data, schema=schema)


def test_minimal_single_repository():
    schema = get_schema()
    data = {"defaults": {}, "repositories": [{"name": "pydriller"}]}
    jsonschema.validate(instance=data, schema=schema)


def test_defaults():
    schema = get_schema()
    data = {
        "defaults": {
            "pydriller": {"since": "", "to": ""},
            "filters": {
                "commit": [
                    {"field": "msg", "filter_value": "some-text", "method": "exact"}
                ]
            },
        },
        "repositories": [{"name": "pydriller"}],
    }
    jsonschema.validate(instance=data, schema=schema)
