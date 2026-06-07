from rich.table import Table
from rich.console import Console
import json

console = Console()

def show_table(image: str, findings: list):
    table = Table(title=f"DockLens Scan Report: {image}")
    table.add_column("Package")
    table.add_column("Version")
    table.add_column("Severity")
    table.add_column("Fix")

    for f in findings:
        table.add_row(
            f["package"],
            f["version"],
            f["severity"],
            f["fix"] or "-"
        )

    console.print(table)


def show_json(image: str, findings: list):
    console.print_json(json.dumps({
        "image": image,
        "findings": findings
    }))

