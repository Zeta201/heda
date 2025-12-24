from pathlib import Path
import subprocess

import requests

GITOPS_ORG = "Zeta201"  # Your GitHub org/user
GITOPS_TOKEN = "<YOUR_PERSONAL_ACCESS_TOKEN>"  # Or fetch from env securely
GITOPS_BASE_URL = "https://api.github.com"

class GitError(Exception):
    pass

def run_git_command(cmd: list[str], cwd: Path = Path(".")):
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        raise GitError(f"Git command failed: {' '.join(cmd)}") from e

