# cli/output.py
# Display functions for DockLens scan results.

from rich.table import Table
from rich.console import Console
import json

console = Console()


def show_table(image: str, findings: list):
    table = Table(title=f"DockLens Scan Report: {image}")
    table.add_column("Package")
    table.add_column("Version")
    table.add_column("Severity")
    table.add_column("CVE")
    table.add_column("EUVD ID")
    table.add_column("EUVD Score")
    table.add_column("Fix version")
    table.add_column("Command")

    for f in findings:
        table.add_row(
            f["package"],
            f["version"],
            f.get("severity", "-"),
            f.get("cve") or "-",
            f.get("euvd_id") or "-",
            str(f.get("euvd_score")) if f.get("euvd_score") else "-",
            f.get("fix") or "-",
            f.get("command") or "-",
        )

    console.print(table)


def show_json(image: str, findings: list):
    console.print_json(json.dumps({
        "image": image,
        "findings": findings,
    }))
