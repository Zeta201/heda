import json
import os
from pathlib import Path
from datetime import datetime
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from dotenv import load_dotenv
load_dotenv()


from heda.config import get_username
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError


BACKEND_URL = os.environ.get("HEDA_BACKEND_URL")
BACKEND_AUTH_TOKEN = os.environ.get("BACKEND_AUTH_TOKEN")

console = Console()
REGISTRY_FILE = Path(".heda/registry.json")


class PublishError(Exception):
    pass


# -----------------------------
# Step context manager
# -----------------------------
from contextlib import contextmanager

@contextmanager
def step(description: str):
    from rich.progress import Progress, SpinnerColumn, TextColumn
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn(f"[green]{{task.description}}[/green]"),
        transient=True,
    ) as progress:
        task = progress.add_task(description, total=None)
        try:
            yield
            progress.update(task, description=f"[green]✓ {description}[/green]")
        except Exception as e:
            progress.update(task, description=f"[red]✗ {description}[/red]")
            raise e


# -----------------------------
# Local registry utils
# -----------------------------
def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"versions": []}
    return json.loads(REGISTRY_FILE.read_text())

def save_registry(registry: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))


# -----------------------------
# Publish CLI
# -----------------------------
def publish_experiment(exp_name: str):
    username = get_username()

    # -----------------------------
    # Step 1: Validate experiment
    # -----------------------------
    with step("Validating experiment.yaml"):
        experiment = load_experiment_yaml(Path("experiment.yaml"))
        validate_experiment(experiment)

    # -----------------------------
    # Step 2: Collect files
    # -----------------------------
    with step("Collecting experiment files"):
        files = collect_publish_files()

    # -----------------------------
    # Step 3: Upload files to backend
    # -----------------------------
    with step("Creating pull request for publishing"):
        multipart_files = [
            ("files", (str(f), f.read_bytes(), "application/octet-stream")) for f in files
        ]

        response = requests.post(
            f"{BACKEND_URL}/publish",
            headers={"X-Auth-Token": BACKEND_AUTH_TOKEN},
            files=multipart_files,
            data={
                "username": username,
                "experiment_name": exp_name,
            },
            timeout=120,
        )

        if response.status_code != 200:
            raise PublishError(response.text)

        payload = response.json()
        experiment_id = payload["experiment_id"]
        pr_url = payload.get("pull_request_url")

    # -----------------------------
    # Step 4: Update local registry
    # -----------------------------
    with step("Updating local registry"):
        registry = load_registry()
        registry["versions"].append(
            {
                "id": experiment_id,
                "timestamp": datetime.utcnow().isoformat(),
                "pr_url": pr_url,
            }
        )
        save_registry(registry)

    console.print(f"\n[bold green]🎉 Experiment '{experiment_id}' proposed successfully![/bold green]")
    console.print(f"[bold blue]Pull Request URL:[/bold blue] {pr_url}")

    return experiment_id, pr_url


def collect_publish_files() -> list[Path]:
    root = Path(".") 
    files = [ root / "experiment.yaml", root / "requirements.txt", root / ".heda/Dockerfile", ] 
    src_dir = root / "src"
    if src_dir.exists(): 
        files.extend(p for p in src_dir.rglob("*") if p.is_file()) 
        return files