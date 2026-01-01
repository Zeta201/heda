from contextlib import contextmanager
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.style import Style

console = Console()

SUCCESS_STYLE = Style(color="green", bold=True)
FAILURE_STYLE = Style(color="red", bold=True)
INFO_STYLE = Style(color="cyan")


@contextmanager
def step(
    description: str,
    *,
    spinner_name: str = "dots",
    console_instance: Console = console,
    success_message: Optional[str] = None,
    failure_message: Optional[str] = None,
    refresh_rate: int = 12,
):
    """
    Context-managed execution step with spinner and final success/failure state.

    Args:
        description: Message shown while the step is running
        spinner_name: Rich spinner type (default: "dots")
        console_instance: Rich Console to render to
        success_message: Optional override for success text
        failure_message: Optional override for failure text
        refresh_rate: Live refresh rate
    """

    spinner = Spinner(
        spinner_name,
        text=Text(description, style=INFO_STYLE),
    )

    with Live(
        spinner,
        console=console_instance,
        refresh_per_second=refresh_rate,
    ):
        try:
            yield
        except Exception as exc:
            spinner.text = Text(
                f"✗ {failure_message or description}",
                style=FAILURE_STYLE,
            )
            console_instance.print(
                f"[red]Error:[/] {exc}",
                highlight=False,
            )
            raise
        else:
            spinner.text = Text(
                f"✓ {success_message or description}",
                style=SUCCESS_STYLE,
            )
