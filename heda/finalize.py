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

CI_WORKFLOW_PATH = Path(".github/workflows/reproduce.yml")

CI_WORKFLOW_CONTENT = """\
name: Reproduce Experiment

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  reproduce:
    runs-on: ubuntu-latest

    steps:
    
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install heda CLI
        run: |
          pip install --upgrade pip
          pip install heda

      - name: Validate experiment spec
        run: |
          heda validate

      - name: Verify experiment (run + claims)
        run: |
          heda verify

      - name: Upload verification artifact
        uses: actions/upload-artifact@v4
        with:
          name: verification
          path: verification.json
"""

README_PATH = Path("README.md")

def get_github_repo() -> str:
    """Get owner/repo dynamically from git remote"""
    try:
        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        if remote.startswith("git@"):
            owner_repo = remote.split(":")[1].replace(".git", "")
        elif remote.startswith("https://"):
            owner_repo = "/".join(remote.split("/")[-2:]).replace(".git", "")
        else:
            owner_repo = "owner/repo"
        return owner_repo
    except subprocess.CalledProcessError:
        return "owner/repo"
 
def add_badge_to_readme():
    owner_repo = get_github_repo()
    badge_markdown = f"![Reproducibility](https://github.com/{owner_repo}/actions/workflows/reproduce.yml/badge.svg)\n"

    if not README_PATH.exists():
        README_PATH.write_text(badge_markdown)
        return

    content = README_PATH.read_text()
    if badge_markdown not in content:
        README_PATH.write_text(badge_markdown + content)
   
def generate_ci_workflow():
    if CI_WORKFLOW_PATH.exists():
        existing = CI_WORKFLOW_PATH.read_text()
        if existing != CI_WORKFLOW_CONTENT:
            raise ExperimentFinalizeError(
                "Existing CI workflow differs from canonical heda workflow. "
                "Refusing to overwrite."
            )
        return  

    CI_WORKFLOW_PATH.parent.mkdir(parents=True, exist_ok=True)
    CI_WORKFLOW_PATH.write_text(CI_WORKFLOW_CONTENT)

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
    
    generate_ci_workflow()
    add_badge_to_readme()


