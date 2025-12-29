import json
import os
from pathlib import Path
from datetime import datetime
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from dotenv import load_dotenv

from heda.utils.auth import get_username
from heda.utils.exp_utils import get_dockerfile_file_path, get_exp_path, get_requirement_file_path
from heda.utils.httputils import RequestError, post_multipart
load_dotenv()


# from heda.config import get_username
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError


BACKEND_URL = os.environ.get("HEDA_BACKEND_URL")

console = Console()
REGISTRY_FILE = Path(".heda/registry.json")


class PublishError(Exception):
    pass


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


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"versions": []}
    return json.loads(REGISTRY_FILE.read_text())

def save_registry(registry: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))


def publish_experiment(exp_name: str):

    with step("Validating experiment.yaml"):
        experiment = load_experiment_yaml(Path("experiment.yaml"))
        validate_experiment(experiment)


    with step("Collecting experiment files"):
        files = collect_publish_files()

    with step("Creating pull request for publishing"):
        try:
            payload = post_multipart(
        endpoint="/publish",
        files=files,
        form_data={
            "experiment_name": exp_name
        },
        timeout=120
    )
        except RequestError as e:
            raise PublishError(f"Publishing failed: {e}")

        experiment_id = payload["experiment_id"]
        pr_url = payload["pr_url"]


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
    files = [ get_exp_path(), get_requirement_file_path(), get_dockerfile_file_path()] 
    src_dir = root / "src"
    data_dir = root / "data"
    
    if src_dir.exists(): 
        files.extend(p for p in src_dir.rglob("*") if p.is_file()) 
    if data_dir.exists():
        files.extend(p for p in data_dir.rglob("*") if p.is_file()) 
    
    return files
        