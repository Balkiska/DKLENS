# cli/menu.py
# Main CLI entry point for DockLens.

import typer
from cli.output import show_table, show_json
from scanner.docker_image import validate_and_pull_image
from scanner.extractor import extract_filesystem
from scanner.packages import extract_packages
from vulns.scanner import scan_packages
from cve.cpe import enrich_packages

app = typer.Typer(help="DockLens - Docker Image Security Scanner")


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
