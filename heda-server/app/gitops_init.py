from app.github import put_file
from app.config import get_admin_gh
from app.templates.pr_finalize import pr_finalize_template
from app.templates.pr_verify import pr_verify_template

def initialize_gitops_repo(repo_full_name: str):
    gh = get_admin_gh()

    # Create pr-verify workflow
    put_file(
        gh,
        repo_full_name,
        ".github/workflows/pr-verify.yml",
        pr_verify_template,
        "chore: add PR verification workflow",
    )

    # Create main-finalize workflow
    put_file(
        gh,
        repo_full_name,
        ".github/workflows/main-finalize.yml",
        pr_finalize_template,
        "chore: add main finalize workflow",
    )
