from pathlib import Path
import subprocess

import requests
import yaml

GITOPS_ORG = "Zeta201"  # Your GitHub org/user
GITOPS_TOKEN = "<YOUR_PERSONAL_ACCESS_TOKEN>"  # Or fetch from env securely
GITOPS_BASE_URL = "https://api.github.com"

class GitError(Exception):
    pass

def run_git_command(cmd: list[str], cwd: Path = Path(".")):
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        raise GitError(f"Git command failed: {' '.join(cmd)}") from e

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