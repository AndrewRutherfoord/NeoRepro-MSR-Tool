import yaml
import jsonschema
import json

# Load the YAML file
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Load the JSON schema
with open('./schema.json', 'r') as f:
    schema = json.load(f)

# Validate the YAML file against the schema
try:
    jsonschema.validate(instance=config, schema=schema)
    print("YAML file is valid.")
except jsonschema.exceptions.ValidationError as err:
    print(f"YAML file is invalid: {err.message}")
