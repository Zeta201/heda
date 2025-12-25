import os
import subprocess
import requests
import typer
from pathlib import Path
from heda.check import ClaimCheckError, check_claims
from heda.publish import PublishError, publish_experiment
from heda.utils import get_experiment_name
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError
from heda.run import run_experiment, ExperimentRunError
from heda.finalize import finalize_experiment, ExperimentFinalizeError
from heda.verify import VerificationError, verify_experiment
from heda.config import get_username
from heda.templates.experiment_yaml import experiment_yaml_template
from heda.templates.sample_code import sample_code_template
from heda.ui.progress import step
from rich.console import Console

from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = os.environ.get("HEDA_BACKEND_URL")
BACKEND_AUTH_TOKEN = os.environ.get("BACKEND_AUTH_TOKEN")

app = typer.Typer(help="HEDA CLI")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """HEDA CLI."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


console = Console()

@app.command()
def init(exp_name: str):
    """
    Initialize a new experiment directory
    """
    username = get_username()
    base_path = Path(exp_name)

    if base_path.exists():
        console.print(f"[red]✗ directory '{exp_name}' already exists[/red]")
        raise typer.Exit(code=1)

    with step("Creating experiment directory structure"):
        (base_path / "src").mkdir(parents=True)
        (base_path / "data").mkdir()
        (base_path / "outputs").mkdir()
        (base_path / ".heda").mkdir()

    with step("Writing template files"):
        (base_path / "requirements.txt").write_text("# Add dependencies here\n")
        experiment_yaml = experiment_yaml_template.format(exp_name=exp_name)
        (base_path / "experiment.yaml").write_text(experiment_yaml)
        (base_path / "src" / "main.py").write_text(sample_code_template)

    with step("Initializing local Git repository"):
        
        subprocess.run(["git", "init"], cwd=base_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], cwd=base_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial experiment structure"], cwd=base_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "branch", "-M", "main"], cwd=base_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with step("Creating remote GitOps repository"):
        response = requests.post(
            f"{BACKEND_URL}/init",
            headers={"x-auth-token": BACKEND_AUTH_TOKEN},
            json={"username": username, "experiment_name": exp_name},
            timeout=10,
        )

        if response.status_code != 200:
            raise RuntimeError(response.text)

        remote_url = response.json()["repo_url"]

    with step("Linking remote repository"):
        subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=base_path,
            check=True
        )

    console.print(
        f"\n[bold green]🎉 Experiment '{exp_name}' initialized successfully![/bold green]"
    )

@app.command()
def validate():
    """
    Validate experiment.yaml against the schema.
    """
    experiment_path = Path("experiment.yaml")

    try:
        data = load_experiment_yaml(experiment_path)
        validate_experiment(data)
    except ExperimentValidationError as e:
        typer.echo(f"Validation failed: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("experiment.yaml is valid")

@app.command()
def finalize():
    try:
        finalize_experiment()
    except ExperimentFinalizeError as e:
        typer.echo(f"Finalize failed: {e}", err=True)
        raise typer.Exit(1)

    typer.echo("Experiment finalized (Dockerfile locked)")
    
@app.command()
def run():
    """
    Run the experiment inside Docker.
    """
    try:
        run_experiment()
    except ExperimentRunError as e:
        typer.echo(f"Run failed: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("Experiment ran successfully")

@app.command()
def check():
    """
    Check experiment outputs against declared claims.
    """
    try:
        check_claims()
    except ClaimCheckError as e:
        typer.echo(f"Claim check failed:\n{e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("All claims satisfied")

@app.command()
def verify():
    """
    Run experiment, evaluate claims, and produce verification.json.
    """
    try:
        verify_experiment()
    except VerificationError as e:
        typer.echo(f"Verification failed: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("Verification succeeded")

@app.command("publish")
def publish():
    """
    Publish the current experiment:
    - Validate
    - Generate unique ID
    - Commit + tag in Git
    - Update registry
    - Push to GitHub
    """
    
    try:
        exp_id = publish_experiment(exp_name=get_experiment_name())
        typer.secho(f"Experiment published successfully! ID: {exp_id}", fg=typer.colors.GREEN)
    except PublishError as e:
        typer.secho(f"[❌] Publish failed: {e}", fg=typer.colors.RED)

# @app.command("list")
# def repro_list():
#     """
#     List all published experiment versions.
#     """
#     list_versions()

# @app.command("checkout")
# def repro_checkout(version_id: str):
#     """
#     Switch to a specific experiment version.
#     """
#     try:
#         checkout_version(version_id)
#     except PublishError as e:
#         typer.secho(f"[❌] Checkout failed: {e}", fg=typer.colors.RED)
