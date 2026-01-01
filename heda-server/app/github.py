from app.config import get_admin_gh, get_admin_org
from github import Github

def create_repo(repo_name: str) -> str:
    """
    Create an empty GitOps repository for experiment proposals.
    """
    org = get_admin_org()

    repo = org.create_repo(
        name=repo_name,
        private=False,
        description=f"HEDA GitOps repo for {repo_name}",
        auto_init=False,
        allow_squash_merge=True,
        allow_merge_commit=True,
        allow_rebase_merge=True,
    )

    return repo.full_name

def put_file(
    gh: Github,
    repo_full_name: str,
    path: str,
    content: str,
    message: str,
    branch: str = "main",
):
    repo = gh.get_repo(repo_full_name)

    repo.create_file(
        path=path,
        message=message,
        content=content,
        branch=branch,
    )

def protect_main_branch(repo_full_name: str):
    """
    Enforce PR-only merges and block direct pushes to main.
    """
    gh = get_admin_gh()
    repo = gh.get_repo(repo_full_name)


    branch = repo.get_branch("main")

    branch.edit_protection(
        strict= True,
        contexts= ["verify"],
        # === Admin + history rules ===
        enforce_admins=True,
        required_linear_history=True,

        # === Dangerous operations ===
        allow_force_pushes=False,
        allow_deletions=False,
    )


