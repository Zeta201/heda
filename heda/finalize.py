from pathlib import Path
import hashlib
import json
from heda.ui.progress import step
from heda.utils.exp_utils import get_dockerfile_file_path, get_exp_path, get_requirement_file_path
from heda.validate import load_experiment_yaml, validate_experiment
from heda.templates.dockerfile_sample import dockerfile_template

class ExperimentFinalizeError(Exception):
    pass

def finalize_experiment():
    root = Path(".")
    heda_dir = root / ".heda"
    heda_dir.mkdir(exist_ok=True)

    with step("Loading and validating experiment.yaml"):
        exp_path = get_exp_path()
        _ = get_requirement_file_path()
        data = load_experiment_yaml(exp_path)
        validate_experiment(data)

    with step("Generating Dockerfile"):
        entrypoint = data["procedure"]["entrypoint"]
        entrypoint_json = json.dumps(entrypoint.split())
        dockerfile_content = dockerfile_template.format(entrypoint=entrypoint_json)
        dockerfile_path = get_dockerfile_file_path()
        dockerfile_path.write_text(dockerfile_content)

    with step("Locking Dockerfile digest"):
        digest = hashlib.sha256(dockerfile_content.encode()).hexdigest()
        (heda_dir / "dockerfile.lock").write_text(digest)
