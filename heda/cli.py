import shutil
import time
import requests
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
from heda.config import load_config, onboard_user, save_config
from heda.ui.progress import step
from rich.console import Console

from dotenv import load_dotenv
load_dotenv()

# --- Auth0 Configuration ---
AUTH0_DOMAIN = "dev-752bai1ktwy78hwp.us.auth0.com"
CLIENT_ID = "zInOH0ENavRtYvhYVKOpkqSftmm782Vx"
AUDIENCE = "https://heda.example.com/api"
SCOPES = "openid profile email read:org"

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
    base_path = Path(exp_name)
    local_initialized = False

    # Pre-flight checks (no spinners)
    if base_path.exists():
        console.print(
            f"[red]✗ Directory '{exp_name}' already exists[/red]"
        )
        raise typer.Exit(code=1)
    try: 
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
            local_initialized = True

        with step(
            "Creating remote GitOps repository",
            success_message="Remote GitOps repository created",
        ):
            response = post_json(
                "/init",
                {
                    "experiment_name": exp_name,
                },
            )
            remote_url = response["repo_url"]

        with step(
            "Linking remote repository",
            success_message="Remote repository linked",
        ):
            git_remote_add(base_path, "origin", remote_url)
    except Exception as e:
        console.print(f"[red]Initialization failed:[/red] {e}")
        
        console.print("[yellow]Cleaning up partial initialization...[/yellow]")
        if local_initialized and base_path.exists():
            try:
                shutil.rmtree(base_path)
                console.print(f"✓ Removed local directory '{exp_name}'")
            except Exception as cleanup_err:
                console.print(f"[red]Failed to remove directory '{exp_name}':[/red] {cleanup_err}")

        raise typer.Exit(code=1)

    console.print()
    console.print(
        f"[bold green]✓ Experiment '{exp_name}' initialized successfully![/bold green]"
    )

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

@app.command("config")
def config():
    """
    One-time HEDA configuration and onboarding.
    """
    onboard_user()
    
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


@app.command()
def login():
    """
    Login via Auth0 GitHub OAuth (Device Flow)
    """
    console.print("[bold]HEDA Login via Auth0 GitHub OAuth[/bold]\n")

    # Request device code
    resp = requests.post(f"https://{AUTH0_DOMAIN}/oauth/device/code", data={
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "audience": AUDIENCE
    }).json()

    console.print(f"Open [bold]{resp['verification_uri_complete']}[/bold] in your browser to authenticate")

    # Poll token endpoint
    while True:
        time.sleep(resp["interval"])
        token_resp = requests.post(f"https://{AUTH0_DOMAIN}/oauth/token", data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": resp["device_code"],
            "client_id": CLIENT_ID
        }).json()

        if "access_token" in token_resp:
            config = load_config()
            config.update({
                "access_token": token_resp["access_token"],
                "refresh_token": token_resp.get("refresh_token"),
                "expires_in": token_resp.get("expires_in"),
                "token_type": token_resp.get("token_type", "Bearer"),
            })
            save_config(config)

            console.print("\n✅ Login successful!\n")
            break

        if token_resp.get("error") == "authorization_pending":
            continue

        raise RuntimeError(f"Auth failed: {token_resp}")
