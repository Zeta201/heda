import hashlib
from pathlib import Path
import json
import subprocess
from heda.validate import load_experiment_yaml, validate_experiment

class ExperimentFinalizeError(Exception):
    pass

DOCKERFILE_TEMPLATE = """\
FROM python:3.11-slim

WORKDIR /exp
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD {entrypoint}
"""

README_PATH = Path("README.md")

def finalize_experiment():
    root = Path(".")
    heda_dir = root / ".heda"
    heda_dir.mkdir(exist_ok=True)

    exp_path = root / "experiment.yaml"
    reqs = root / "requirements.txt"

    if not exp_path.exists():
        raise ExperimentFinalizeError("experiment.yaml not found")

    if not reqs.exists():
        raise ExperimentFinalizeError("requirements.txt not found")

    data = load_experiment_yaml(exp_path)
    validate_experiment(data)

    entrypoint = data["procedure"]["entrypoint"]
    entrypoint_json = json.dumps(entrypoint.split())


    dockerfile_content = DOCKERFILE_TEMPLATE.format(
        entrypoint=entrypoint_json
    )

    dockerfile_path = heda_dir / "Dockerfile"
    dockerfile_path.write_text(dockerfile_content)

    digest = hashlib.sha256(dockerfile_content.encode()).hexdigest()
    (heda_dir / "dockerfile.lock").write_text(digest)


