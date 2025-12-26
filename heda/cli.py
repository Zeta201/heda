import typer
from pathlib import Path
from heda.check import ClaimCheckError, check_claims
from heda.utils.exp_utils import get_experiment_name
from heda.utils.git_utils import git_init, git_remote_add
from heda.utils.httputils import post_json
from heda.init import create_directory_structure, create_template_files
from heda.publish import PublishError, publish_experiment
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError
from heda.run import run_experiment, ExperimentRunError
from heda.finalize import finalize_experiment, ExperimentFinalizeError
from heda.verify import VerificationError, verify_experiment
from heda.config import get_username
from heda.ui.progress import step
from rich.console import Console

from dotenv import load_dotenv
load_dotenv()

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
    Initialize a new experiment directory.
    """
    username = get_username()
    base_path = Path(exp_name)

    # Pre-flight checks (no spinners)
    if base_path.exists():
        console.print(
            f"[red]✗ Directory '{exp_name}' already exists[/red]"
        )
        raise typer.Exit(code=1)

    with step(
        "Creating experiment directory structure",
        success_message="Directory structure created",
    ):
        create_directory_structure(base_path)

    with step(
        "Writing template files",
        success_message="Template files written",
    ):
        create_template_files(base_path, exp_name)

    with step(
        "Initializing local Git repository",
        success_message="Local Git repository initialized",
    ):
        git_init(base_path)

    with step(
        "Creating remote GitOps repository",
        success_message="Remote GitOps repository created",
    ):
        response = post_json(
            "/init",
            {
                "username": username,
                "experiment_name": exp_name,
            },
        )
        remote_url = response["repo_url"]

    with step(
        "Linking remote repository",
        success_message="Remote repository linked",
    ):
        git_remote_add(base_path, "origin", remote_url)

    console.print()
    console.print(
        f"[bold green]✓ Experiment '{exp_name}' initialized successfully![/bold green]"
    )

from pathlib import Path
import typer

@app.command()
def validate():
    """
    Validate experiment.yaml against the schema.
    """
    experiment_path = Path("experiment.yaml")

    try:
        with step(
            "Loading experiment.yaml",
            success_message="experiment.yaml loaded",
            failure_message="Failed to load experiment.yaml",
        ):
            data = load_experiment_yaml(experiment_path)

        with step(
            "Validating experiment.yaml schema",
            success_message="Schema validation passed",
            failure_message="Schema validation failed",
        ):
            validate_experiment(data)

    except ExperimentValidationError as e:
        # Step already shows ✗ — this is the final user-facing error
        console.print(f"[red]Validation failed:[/] {e}")
        raise typer.Exit(code=1)

    console.print("[bold green]✓ experiment.yaml is valid[/bold green]")

@app.command()
def finalize():
    """
    Finalize the experiment by validating inputs and locking the Dockerfile.
    """
    try:
        with step(
            "Finalizing experiment",
            success_message="Experiment finalized",
            failure_message="Experiment finalization failed",
        ):
            finalize_experiment()

    except ExperimentFinalizeError as e:
        # Step already renders ✗ — print a concise final error
        console.print(f"[red]Finalize failed:[/] {e}")
        raise typer.Exit(code=1)

    console.print(
        "[bold green]✓ Experiment finalized (Dockerfile locked)[/bold green]"
    )
   
@app.command()
def run():
    """
    Run the experiment inside Docker.
    """
    try:
        run_experiment()
    except ExperimentRunError as e:
        console.print(f"[red]Run failed:[/] {e}")
        raise typer.Exit(code=1)

    console.print("[bold green]✓ Experiment completed successfully[/bold green]")

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
