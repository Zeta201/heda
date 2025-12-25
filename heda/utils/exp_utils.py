from pathlib import Path
import yaml

def get_experiment_name(experiment_file: Path = Path("experiment.yaml")) -> str:
    """
    Reads experiment.yaml and returns the value of 'name'.
    """
    if not experiment_file.exists():
        raise FileNotFoundError(f"{experiment_file} does not exist")

    with experiment_file.open("r") as f:
        data = yaml.safe_load(f)

    if "name" not in data:
        raise KeyError("'name' key not found in experiment.yaml")

    return data["name"]

def get_exp_path() -> Path:
    exp_path = Path(".") / "experiment.yaml"
    if not exp_path.exists():
        raise FileNotFoundError("experiment.yaml not found")
    return exp_path

def get_requirement_file_path() -> Path:
    req_path = Path(".") / "requirements.txt"
    if not req_path.exists():
        raise FileNotFoundError("requirements.txt not found")
    return req_path

def get_dockerfile_file_path(heda_dir: Path) -> Path:
    return heda_dir / "Dockerfile"
 