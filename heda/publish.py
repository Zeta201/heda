import hashlib
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

import requests

from heda.utils import run_git_command
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError


from dotenv import load_dotenv
load_dotenv()

# Local registry file to store versions metadata
REGISTRY_FILE = Path(".heda/registry.json")
BACKEND_URL = os.environ.get("HEDA_BACKEND_URL")
BACKEND_AUTH_TOKEN = os.environ.get("BACKEND_AUTH_TOKEN")

REGISTRY_FILE = Path(".heda/registry.json")

class PublishError(Exception):
    pass

def collect_publish_files() -> list[Path]:
    root = Path(".")

    files = [
        root / "experiment.yaml",
        root / "requirements.txt",
        root / ".heda/Dockerfile",
    ]

    src_dir = root / "src"
    if src_dir.exists():
        files.extend(p for p in src_dir.rglob("*") if p.is_file())

    return files

def publish_experiment(username: str, exp_name: str) -> str:
    """
    Publish experiment via backend.
    Backend is the source of truth for:
    - experiment ID
    - commit
    - tag
    """

    # 1. Validate
    experiment = load_experiment_yaml(Path("experiment.yaml"))
    validate_experiment(experiment)


    # 2. Collect files
    files = collect_publish_files()

    # 3. Call backend
    multipart_files = []
    for f in files:
        multipart_files.append(
            (
                "files",
                (
                    str(f),
                    f.read_bytes(),
                    "application/octet-stream",
                ),
            )
        )

    response = requests.post(
    f"{BACKEND_URL}/publish",
    headers={"X-Auth-Token": BACKEND_AUTH_TOKEN},
    files=multipart_files,
    data={
        "username": username,
        "experiment_name": exp_name,
    },
    timeout=60,
)

    if response.status_code != 200:
        raise PublishError(response.text)

    payload = response.json()
    experiment_id = payload["experiment_id"]

    print(f"[✔] Published experiment: {experiment_id}")

    # 4. Mirror tag locally
    subprocess.run(
        [
            "git",
            "tag",
            "-a",
            experiment_id,
            "-m",
            f"Published experiment {experiment_id}",
        ],
        check=True,
    )
    # 6. Update local registry
    registry = load_registry()
    registry["versions"].append(
        {
            "id": experiment_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    save_registry(registry)

    return experiment_id

def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"versions": []}
    return json.loads(REGISTRY_FILE.read_text())


def save_registry(registry: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))

def list_versions():
    """List all published versions locally""" 
    registry = load_registry() 
    for v in registry.get("versions", []): 
        print(f"{v['id']} - {v['timestamp']}") 

def checkout_version(version_id: str): 
    """Switch to a specific version of the experiment""" 
    # Use Git checkout 
    run_git_command(["git", "checkout", version_id]) 
    print(f"[✔] Checked out experiment version: {version_id}")