from contextlib import contextmanager
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text

console = Console()

@contextmanager
def step(description: str):
    """
    Reusable step with spinner → success / failure
    """
    spinner = Spinner("dots", text=description)
    status_text = Text(description)

    with Live(spinner, console=console, refresh_per_second=12):
        try:
            yield
        except Exception:
            spinner.text = f"[red]✗ {description}[/red]"
            raise
        else:
            spinner.text = f"[green]✓ {description}[/green]"
