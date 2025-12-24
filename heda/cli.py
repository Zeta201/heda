import typer
from pathlib import Path
from heda.check import ClaimCheckError, check_claims
from heda.validate import load_experiment_yaml, validate_experiment, ExperimentValidationError
from heda.run import run_experiment, ExperimentRunError
from heda.finalize import finalize_experiment, ExperimentFinalizeError
from heda.verify import VerificationError, verify_experiment

app = typer.Typer(help="HEDA CLI")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """HEDA CLI root."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

@app.command()
def hello():
    """Sanity check command."""
    typer.echo("HEDA CLI is working")

@app.command()
def init(name: str):
    """
    Initialize a new experiment directory
    
    :name str: Name of the experiment
    """
    base_path = Path(name)
    
    if base_path.exists():
        typer.echo(f"Error: directory '{name}' already exists.", err=True)
        raise typer.Exit(code=1)
    
    # Create directory structure
    (base_path / "src").mkdir(parents=True)
    (base_path / "data").mkdir()
    (base_path / "outputs").mkdir()
    (base_path / ".heda").mkdir()
    
    (base_path / "requirements.txt").write_text("# Add dependencies here\n")

    # experiment.yaml
    experiment_yaml = """\
name: example_experiment
procedure:
  entrypoint: python src/main.py
claims:
  - metric: accuracy
    operator: ">="
    value: 0.8
"""

    # run.py
    main_py = """\
import json
from pathlib import Path

# Dummy experiment logic
accuracy = 0.85

outputs_dir = Path("outputs")
outputs_dir.mkdir(exist_ok=True)

with open(outputs_dir / "metrics.json", "w") as f:
    json.dump({"accuracy": accuracy}, f)
"""
    # Write files
    (base_path / "experiment.yaml").write_text(experiment_yaml)
    (base_path / "src" / "main.py").write_text(main_py)

    typer.echo(f"Initialized new experiment in '{name}'")
    
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
