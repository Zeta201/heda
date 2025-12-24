from pathlib import Path
import yaml
from jsonschema import validate, ValidationError
from heda.schema import EXPERIMENT_SCHEMA


class ExperimentValidationError(Exception):
    pass


def load_experiment_yaml(path: Path) -> dict:
    if not path.exists():
        raise ExperimentValidationError("experiment.yaml not found")

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ExperimentValidationError(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise ExperimentValidationError("experiment.yaml must be a YAML object")

    return data


def validate_experiment(data: dict) -> None:
    try:
        validate(instance=data, schema=EXPERIMENT_SCHEMA)
    except ValidationError as e:
        raise ExperimentValidationError(e.message)
