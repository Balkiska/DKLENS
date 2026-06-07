import typer
from cli.output import show_table, show_json

app = typer.Typer(help="DockLens - Docker Image Security Scanner")

@app.callback()
def main():
    """
    DockLens CLI root command.
    """
    pass

@app.command()
def scan(
    image: str = typer.Argument(..., help="Docker image to scan"),
    format: str = typer.Option("table", help="Output format: table|json"),
):
    """
    Scan a Docker image for known vulnerabilities.
    """
    typer.echo("Starting DockLens scan...")
    typer.echo(f"Image: {image}")

    # TODO: plug real scanner here
    # findings = extract_packages(image)
    findings = []

    if not findings:
        typer.echo("Scanner not implemented yet. Run tests/test_output.py to test display.")
        return

    if format == "json":
        show_json(image, findings)
    else:
        show_table(image, findings)
