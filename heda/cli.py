import os
import subprocess
import requests
import typer
from pathlib import Path
from heda.check import ClaimCheckError, check_claims
from heda.publish import PublishError, checkout_version, list_versions, publish_experiment
from heda.templates import experiment_yaml, sample_code
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError
from heda.run import run_experiment, ExperimentRunError
from heda.finalize import finalize_experiment, ExperimentFinalizeError
from heda.verify import VerificationError, verify_experiment
from heda.config import get_username

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

@app.command()
def init(exp_name: str):
    """
    Initialize a new experiment directory
    """
    username = get_username()
    base_path = Path(exp_name)
    
    if base_path.exists():
        typer.echo(f"Error: directory '{exp_name}' already exists.", err=True)
        raise typer.Exit(code=1)
    
    # Create directory structure
    (base_path / "src").mkdir(parents=True)
    (base_path / "data").mkdir()
    (base_path / "outputs").mkdir()
    (base_path / ".heda").mkdir()
    
    (base_path / "requirements.txt").write_text("# Add dependencies here\n")

    # Write files
    experiment_yaml = experiment_yaml.format(exp_name=exp_name)
    (base_path / "experiment.yaml").write_text(experiment_yaml)
    (base_path / "src" / "main.py").write_text(sample_code)
    
     # Initialize local Git repo
    subprocess.run(["git", "init"], cwd=base_path, check=True)

    # Initialize local Git repo
    subprocess.run(["git", "init"], cwd=base_path, check=True)
    subprocess.run(["git", "add", "."], cwd=base_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial experiment structure"], cwd=base_path, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=base_path, check=True)

    # Call backend to create remote GitOps repo with workflow
    response = requests.post(
        f"{BACKEND_URL}/init" ,
        headers={"x-auth-token": BACKEND_AUTH_TOKEN},
        json={"username": username, "experiment_name": exp_name}
    )
    if response.status_code != 200:
        typer.echo(f"Failed to create gitops repo: {response.text}", err=True)
        raise typer.Exit(code=1)

    remote_url = response.json()["repo_url"]
    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=base_path, check=True)
    typer.echo(f"Initialized experiment '{exp_name}'")
    
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
    username = get_username()
    
    try:
        exp_id = publish_experiment(username=username, exp_name="my_test_experiment")
        typer.secho(f"Experiment published successfully! ID: {exp_id}", fg=typer.colors.GREEN)
    except PublishError as e:
        typer.secho(f"[❌] Publish failed: {e}", fg=typer.colors.RED)

@app.command("list")
def repro_list():
    """
    List all published experiment versions.
    """
    list_versions()

@app.command("checkout")
def repro_checkout(version_id: str):
    """
    Switch to a specific experiment version.
    """
    try:
        checkout_version(version_id)
    except PublishError as e:
        typer.secho(f"[❌] Checkout failed: {e}", fg=typer.colors.RED)
