import subprocess
from pathlib import Path

from heda.check import ClaimCheckError, check_claims
from heda.ui.progress import step

class ExperimentRunError(Exception):
    pass

def run_experiment() -> None:
    heda_dir = Path(".heda")
    dockerfile = heda_dir / "Dockerfile"

    with step(
        "Checking experiment finalization state",
        success_message="Experiment is finalized",
        failure_message="Experiment not finalized",
    ):
        if not dockerfile.exists():
            raise ExperimentRunError(
                "Experiment not finalized. Run `heda finalize` first."
            )

    image_tag = "heda-experiment:latest"

    with step(
        "Building Docker image",
        success_message="Docker image built successfully",
        failure_message="Docker image build failed",
    ):
        build_cmd = [
            "docker", "build",
            "-f", str(dockerfile),
            "-t", image_tag,
            ".",
        ]

        result = subprocess.run(build_cmd)
        if result.returncode != 0:
            raise ExperimentRunError("Docker build failed")

    with step(
        "Running experiment container",
        success_message="Experiment container executed",
        failure_message="Experiment execution failed",
    ):
        run_cmd = [
            "docker", "run",
            "--rm",
            "-v",
            f"{Path.cwd()}:/exp",
            image_tag,
        ]

        result = subprocess.run(run_cmd)
        if result.returncode != 0:
            raise ExperimentRunError("Experiment execution failed")

    with step(
        "Validating experiment claims",
        success_message="All experiment claims passed",
        failure_message="Experiment claims validation failed",
    ):
        try:
            check_claims()
        except ClaimCheckError as e:
            raise ExperimentRunError(
                f"Experiment ran, but claims FAILED:\n{e}"
            )