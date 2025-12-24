import subprocess
from pathlib import Path

from heda.check import ClaimCheckError, check_claims

class ExperimentRunError(Exception):
    pass

def run_experiment() -> None:
    
    heda_dir = Path(".heda")
    dockerfile = heda_dir / "Dockerfile"

    if not dockerfile.exists():
        raise ExperimentRunError("Experiment not finalized. Run `heda finalize` first.")

    # Build Docker image
    image_tag = "heda-experiment:latest"

    build = [
        "docker", "build",
        "-f", str(dockerfile),
        "-t", image_tag,
        "."
    ]

    if subprocess.run(build).returncode != 0:
        raise ExperimentRunError("Docker build failed")

    # Run Docker container
    run = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{Path.cwd()}:/exp",
        image_tag,
    ]

    if subprocess.run(run).returncode != 0:
        raise ExperimentRunError("Experiment execution failed")
    
    # After successful docker run
    try:
        check_claims()
    except ClaimCheckError as e:
        raise ExperimentRunError(
            f"Experiment ran, but claims FAILED:\n{e}"
        )
