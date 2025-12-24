import typer
from pathlib import Path

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
    (base_path / "data").mkdir(parents=True)
    (base_path / "outputs").mkdir()
    
    # experiment.yaml
    experiment_yaml = """\
name: example_experiment
procedure:
  entrypoint: python run.py
claims:
  - metric: accuracy
    operator: ">="
    value: 0.8
"""
    # Dockerfile
    dockerfile = """\
FROM python:3.11
WORKDIR /exp
COPY . .
RUN pip install numpy
CMD ["python", "run.py"]
"""

    # run.py
    run_py = """\
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
    (base_path / "Dockerfile").write_text(dockerfile)
    (base_path / "run.py").write_text(run_py)

    typer.echo(f"Initialized new experiment in '{name}'")
    