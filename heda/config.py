import json
from pathlib import Path
import typer
from heda.utils.httputils import post_json, get_json
from rich.console import Console
from rich.spinner import Spinner

CONFIG_DIR = Path.home() / ".config" / "heda"
CONFIG_FILE = CONFIG_DIR / "config.json"

console = Console()

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def onboard_user():

    config = load_config()

    console.print("[bold]HEDA configuration[/bold]\n")

    # Step 1: collect info if missing
    if "github_username" not in config:
        console.print(
            "This will:\n"
            "  • Create your HEDA identity\n"
            "  • Onboard you to HEDA's GitOps system\n"
            "  • Send a GitHub invitation to your github email\n"
        )

        github_username = typer.prompt("Enter your github username")
        
        config.update({
            "github_username": github_username,
            "onboarded": False
        })
        save_config(config)

        with console.status("Sending onboarding request..."):
            post_json("/onboard", {
                "github_username": github_username,
            })

        console.print("\n✓ Invitation sent\n")
        console.print(
            f"A GitHub organization invitation was sent to your github email:\n"
            "Please accept the invitation to continue using HEDA.\n"
            "Run `heda config` again after accepting."
        )
        raise typer.Exit(code=0)

    # Step 2: already configured — check onboarding
    console.print(f"✓ Username: {config['github_username']}")

    with console.status("Checking onboarding status..."):
        status = get_json("/onboard/status", {
            "github_username": config["github_username"]
        })

    if not status["onboarded"]:
        console.print("Invitation still pending\n")
        console.print("Please accept the GitHub invitation sent to your email.")
        raise typer.Exit(code=1)

    # Step 3: mark onboarded
    if not config.get("onboarded"):
        config["onboarded"] = True
        save_config(config)

    console.print("\n🎉 [bold green]HEDA is fully configured![/bold green]")
