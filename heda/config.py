import json
from pathlib import Path
import typer
from heda.utils.httputils import post_json, get_json
from rich.console import Console

CONFIG_DIR = Path.home() / ".config" / "heda"
CONFIG_FILE = CONFIG_DIR / "config.json"

class AuthError(BaseException):
    pass

console = Console()

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def require_login():
    config = load_config()
    if not config.get("access_token"):
        console.print("[red]You are not logged in.[/red]")
        console.print("Run `heda login` to continue.")
        raise typer.Exit(1)

def onboard_user():

    require_login()
    
    try:
        with console.status("Checking onboarding status..."):
            status = get_json("/onboard/status")
    except AuthError:
        console.print("[red]Authentication expired.[/red]")
        console.print("Run `heda login` again.")
        raise typer.Exit(1)
    
    if status["onboarded"]:
        console.print("✓ GitHub organization access confirmed")
        console.print("\n[bold green]HEDA is fully configured![/bold green]")
        return
    
    if status.get("invitation") == "PENDING":
        console.print("GitHub organization invitation pending")
        console.print(
            "An invitation has been sent to your GitHub account.\n"
            "Please accept the invitation and run `heda config` again."
        )
        return
        

    # Step 1: collect info if missing
    console.print(
        "This will:\n"
        "  • Create your HEDA identity\n"
        "  • Onboard you to HEDA's GitOps system\n"
        "  • Send a GitHub invitation to your github email\n"
    )

    with console.status("Sending onboarding request..."):
        post_json("/onboard", {})

    console.print("\n✓ Invitation sent\n")
    console.print(
            f"A GitHub organization invitation was sent to your github email:\n"
            "Please accept the invitation to continue using HEDA.\n"
            "Run `heda config` again after accepting."
        )
    raise typer.Exit(code=0)
