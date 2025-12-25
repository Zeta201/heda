import subprocess
from pathlib import Path
from typing import List, Optional


def run_git_command(
    args: List[str],
    cwd: Optional[Path] = None,
    suppress_output: bool = True
) -> None:
    """
    Run a git command in the specified directory.
    Args:
        args: List of git command arguments, e.g., ["init"], ["add", "."]
        cwd: Path where to run the git command. Defaults to current dir.
        suppress_output: If True, stdout/stderr are suppressed.
    Raises:
        subprocess.CalledProcessError if git command fails.
    """
    kwargs = {"cwd": cwd, "check": True}
    if suppress_output:
        kwargs.update({"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL})

    subprocess.run(["git"] + args, **kwargs)


def git_init(base_path: Path, main_branch: str = "main") -> None:
    """
    Initialize a git repository with an initial commit.
    """
    run_git_command(["init"], cwd=base_path)
    run_git_command(["add", "."], cwd=base_path)
    run_git_command(["commit", "-m", "Initial experiment structure"], cwd=base_path)
    run_git_command(["branch", "-M", main_branch], cwd=base_path)


def git_add_commit(base_path: Path, message: str) -> None:
    """
    Add all changes and commit.
    """
    run_git_command(["add", "."], cwd=base_path)
    run_git_command(["commit", "-m", message], cwd=base_path)


def git_checkout(base_path: Path, branch: str) -> None:
    """
    Checkout a branch.
    """
    run_git_command(["checkout", branch], cwd=base_path)


def git_create_branch(base_path: Path, branch: str) -> None:
    """
    Create a new branch and switch to it.
    """
    run_git_command(["checkout", "-b", branch], cwd=base_path)


def git_remote_add(base_path: Path, name: str, url: str) -> None:
    """
    Add a remote to the repository.
    """
    run_git_command(["remote", "add", name, url], cwd=base_path)
