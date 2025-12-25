import json
from pathlib import Path
import typer

CONFIG_DIR = Path.home() / ".config" / "heda"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def get_username() -> str:
    config = load_config()

    if "username" in config:
        return config["username"]

    # First-time setup
    username = typer.prompt(
        "Enter your preferred HEDA username",
        default=None
    )

    config["username"] = username
    save_config(config)

    typer.secho(f"Username set to '{username}'", fg=typer.colors.GREEN)
    return username
