import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime

from heda.utils import run_git_command
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError

# Local registry file to store versions metadata
REGISTRY_FILE = Path(".heda/registry.json")

class PublishError(Exception):
    pass


def compute_experiment_hash() -> str:
    """Compute SHA-256 hash of experiment.yaml, Dockerfile, and all src/ files."""
    exp_file = Path("experiment.yaml")
    dockerfile = Path(".heda/Dockerfile")
    src_dir = Path("src")

    if not src_dir.exists() or not src_dir.is_dir():
        raise FileNotFoundError("src/ directory not found. Please create it and add your experiment code.")

    src_files = sorted([f for f in src_dir.rglob("*") if f.is_file()])

    files_to_hash = [exp_file, dockerfile] + src_files

    sha = hashlib.sha256()
    for file in files_to_hash:
        with file.open("rb") as f:
            while chunk := f.read(8192):
                sha.update(chunk)

    return sha.hexdigest()

def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {"versions": []}

def save_registry(registry: dict):
    REGISTRY_FILE.parent.mkdir(exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))

def publish_experiment(push: bool = False) -> str:
    """
    Publish current experiment:
    1. Validate experiment
    2. Generate unique ID
    3. Commit + tag in Git
    4. Optionally push to GitHub
    5. Update local registry
    Returns: experiment ID
    """

    # Step 1: Validate experiment
    root = Path(".")
    heda_dir = root / ".heda"
    heda_dir.mkdir(exist_ok=True)

    exp_file = root / "experiment.yaml"
    src_dir = root / "src"
    dockerfile = heda_dir / "Dockerfile"

    if not exp_file.exists():
        raise PublishError("experiment.yaml not found")

    try:
        exp_data = load_experiment_yaml(exp_file)
        validate_experiment(exp_data)
    except ExperimentValidationError as e:
        raise PublishError(f"Experiment validation failed: {e}")

    # Step 2: Generate experiment ID
    exp_hash = compute_experiment_hash()
    timestamp = datetime.utcnow().isoformat()
    experiment_id = f"exp-{timestamp.replace(':','-')}-{exp_hash[:8]}"
    print(f"[✔] Generated experiment ID: {experiment_id}")

    # Stage all relevant files
    files_to_commit = [exp_file, dockerfile, src_dir, REGISTRY_FILE]
    
    # Step 3: Git commit
    try:
        subprocess.run(["git", "add"] + [str(f) for f in files_to_commit], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Publish experiment {experiment_id}"], check=True
        )

        # Optional Git tag
        if push:
            subprocess.run(
                ["git", "tag", "-a", experiment_id, "-m", f"Published experiment {experiment_id}"],
                check=True
            )
            subprocess.run(["git", "push", "origin", "main", "--tags"], check=True)
            print(f"[✔] Experiment published with ID: {experiment_id}")
    except subprocess.CalledProcessError as e:
        print(f"[⚠️] Git operation failed: {e}")

    # Step 6: Update local registry
    registry = load_registry()
    registry["versions"].append({
        "id": experiment_id,
        "timestamp": datetime.utcnow().isoformat(),
        # "files": [str(f) for f in files_to_hash],
    })
    save_registry(registry)
    print("[✔] Registry updated")

    return experiment_id

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
