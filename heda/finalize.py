from pathlib import Path
import hashlib
import json
from heda.ui.progress import step
from heda.utils.exp_utils import get_dockerfile_file_path, get_exp_path, get_requirement_file_path
from heda.validate import load_experiment_yaml, validate_experiment
from heda.templates.dockerfile_sample import dockerfile_template

class ExperimentFinalizeError(Exception):
    pass

def finalize_experiment() -> None:
    root = Path(".")
    heda_dir = root / ".heda"
    heda_dir.mkdir(exist_ok=True)

    with step(
        "Loading and validating experiment.yaml",
        success_message="experiment.yaml validated",
        failure_message="experiment.yaml validation failed",
    ):
        exp_path = get_exp_path()
        _ = get_requirement_file_path()
        data = load_experiment_yaml(exp_path)
        validate_experiment(data)

    with step(
        "Generating Dockerfile",
        success_message="Dockerfile generated",
        failure_message="Dockerfile generation failed",
    ):
        entrypoint = data["procedure"]["entrypoint"]
        entrypoint_json = json.dumps(entrypoint.split())

        dockerfile_content = dockerfile_template.format(
            entrypoint=entrypoint_json
        )

        dockerfile_path = get_dockerfile_file_path()
        dockerfile_path.write_text(dockerfile_content)

    with step(
        "Locking Dockerfile digest",
        success_message="Dockerfile digest locked",
        failure_message="Failed to lock Dockerfile digest",
    ):
        digest = hashlib.sha256(
            dockerfile_content.encode("utf-8")
        ).hexdigest()

        (heda_dir / "dockerfile.lock").write_text(digest)