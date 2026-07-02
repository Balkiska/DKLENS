# cli/menu.py
# Main CLI entry point for DockLens.

import typer
from cli.output import show_table, show_json, export_pdf
from cli.interactive import start as interactive_start
from scanner.docker_image import validate_and_pull_image
from scanner.extractor import extract_filesystem
from scanner.packages import extract_packages
from vulns.scanner import scan_packages
from cve.cpe import enrich_packages

app = typer.Typer(help="DockLens - Docker Image Security Scanner")


@app.command()
def start():
    """Launch the interactive DockLens menu."""
    interactive_start()


@app.callback()
def main():
    pass


@app.command()
def scan(
    image: str = typer.Argument(..., help="Docker image to scan"),
    format: str = typer.Option("table", help="Output format: table|json"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass the local vulnerability cache"
    ),
    export: str = typer.Option(
        None, "--export", help="Export to file: rapport.pdf or rapport.json"
    ),
):
    """
    Scan a Docker image for known vulnerabilities.
    """
    typer.echo(f"Starting scan for: {image}")

    validate_and_pull_image(image)
    fs_path = extract_filesystem(image)
    packages = extract_packages(str(fs_path))
    packages = enrich_packages(packages)

    typer.echo(f"Found {len(packages)} packages. Checking vulnerabilities...")

    findings = scan_packages(packages, no_cache=no_cache)

    if format == "json":
        show_json(image, findings)
    else:
        show_table(image, findings)

    if export:
        if export.endswith(".pdf"):
            export_pdf(image, findings, export)
            typer.echo(f"PDF report saved: {export}")
        elif export.endswith(".json"):
            import json

            with open(export, "w") as f:
                json.dump({"image": image, "findings": findings}, f, indent=2)
            typer.echo(f"JSON report saved: {export}")
