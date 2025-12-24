import typer

app = typer.Typer(help="HEDA CLI")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """HEDA CLI root."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

@app.command()
def hello():
    """Sanity check command."""
    typer.echo("HEDA CLI is working")
