import json
import sys

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.table import Table
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.utils import get_style

from scanner.docker_image import validate_and_pull_image, get_docker_client
from scanner.extractor import extract_filesystem
from scanner.packages import extract_packages
from vulns.scanner import scan_packages
from cve.cpe import enrich_packages
from cli.output import export_pdf

ROSE = "#785964"

console = Console()

TITLE = r"""
    ____                      __      __
   / __ \   ____     _____   / /__   / /  ___     ____     _____
  / / / /  / __ \   / ___/  / //_/  / /  / _ \   / __ \   / ___/
 / /_/ /  / /_/ /  / /__   / ,<    / /  /  __/  / / / /  (__  )
/_____/   \____/   \___/  /_/|_|  /_/   \___/  /_/ /_/  /____/
"""

STYLE = get_style(
    {
        "questionmark": ROSE,
        "answermark": ROSE,
        "answer": ROSE,
        "input": ROSE,
        "pointer": ROSE,
        "checkbox": ROSE,
        "marker": ROSE,
        "instruction": ROSE,
    }
)

NO_VULN_MESSAGE = r"""✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿

                            /\___/\
                           ( =^.^= )
                           ("")_("")

           ❀ Your selected image is perfectly safe. ❀
               ✿ No vulnerabilities were detected. ✿

✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿･ﾟ* ✧･ﾟ* ✿"""

SEVERITY_COLOR = {
    "CRITICAL": "bright_red",
    "HIGH": "red3",
    "MEDIUM": "dark_orange",
    "LOW": "yellow3",
    "UNKNOWN": "grey66",
    "NONE": "dim",
}


def _show_title():
    content = (
        f"[{ROSE}]{TITLE}[/{ROSE}]\n\n[{ROSE}]  Docker Image Security Scanner[/{ROSE}]"
    )
    console.print(Panel(content, border_style=ROSE, expand=True))


def _list_local_images() -> list:
    client = get_docker_client()
    images = []
    for img in client.images.list():
        for tag in img.tags:
            if "<none>" not in tag:
                images.append(tag)
    return sorted(images)


def _run_scan(image: str) -> tuple:
    with Progress(
        SpinnerColumn(style=Style(color=ROSE)),
        TextColumn(f"[{ROSE}]{{task.description}}[/{ROSE}]"),
        console=console,
    ) as progress:
        task = progress.add_task("Validating image...", total=None)
        validate_and_pull_image(image)

        progress.update(task, description="Extracting filesystem...")
        fs_path = extract_filesystem(image)

        progress.update(task, description="Reading packages...")
        packages = extract_packages(str(fs_path))
        packages = enrich_packages(packages)

        progress.update(
            task, description=f"Scanning {len(packages)} packages for CVEs..."
        )
        findings = scan_packages(packages)

    return findings, len(packages)


def _show_results(
    image: str, findings: list, packages_count: int, severity_filter: str = None
):
    displayed = [f for f in findings if f["severity"] != "NONE"]
    if severity_filter:
        displayed = [f for f in displayed if f["severity"] == severity_filter]

    label = f" ({severity_filter} only)" if severity_filter else ""
    vuln_color = "red" if len(displayed) > 0 else "cyan"
    console.print(
        f"\n[{ROSE}]Image:[/{ROSE}] {image}  "
        f"[{ROSE}]Packages:[/{ROSE}] {packages_count}  "
        f"[{ROSE}]Vulnerabilities:[/{ROSE}] [{vuln_color}]{len(displayed)}{label}[/{vuln_color}]\n"
    )

    table = Table(show_header=True, header_style=f"bold {ROSE}", border_style=ROSE)
    table.add_column("Package")
    table.add_column("Version")
    table.add_column("Severity")
    table.add_column("CVE")
    table.add_column("CPE")
    table.add_column("Fixed in")
    table.add_column("Command")
    table.add_column("EUVD ID")
    table.add_column("Advisory")

    for f in displayed:
        sev = f["severity"]
        color = SEVERITY_COLOR.get(sev, "white")
        table.add_row(
            f.get("package") or "-",
            f.get("version") or "-",
            f"[{color}]{sev}[/{color}]",
            f.get("cve") or "-",
            f.get("cpe") or "-",
            f.get("fix") or "-",
            f.get("command") or "-",
            f.get("euvd_id") or "-",
            f.get("advisory_url") or "-",
        )

    if not displayed:
        if severity_filter:
            console.print(
                f"[{ROSE}]No {severity_filter} vulnerabilities found.[/{ROSE}]\n"
            )
        else:
            console.print(
                Panel(
                    Align.center(NO_VULN_MESSAGE),
                    style=ROSE,
                    border_style=ROSE,
                    expand=True,
                )
            )
    else:
        console.print(table)


def start():
    try:
        _show_title()

        while True:
            with Progress(
                SpinnerColumn(style=Style(color=ROSE)),
                TextColumn(f"[{ROSE}]Listing local Docker images...[/{ROSE}]"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("", total=None)
                images = _list_local_images()

            if not images:
                console.print(
                    f"[{ROSE}]No local Docker images found. Pull one first: docker pull <image>[/{ROSE}]"
                )
                sys.exit(0)

            choices = [Choice(value=img, name=img) for img in images]
            choices.append(Choice(value=None, name="[Quit]"))

            selected = inquirer.select(
                message="Select an image to scan:",
                choices=choices,
                style=STYLE,
                pointer="❯",
            ).execute()

            if selected is None:
                console.print(f"\n[{ROSE}]Goodbye![/{ROSE}]")
                break

            findings, packages_count = _run_scan(selected)
            _show_results(selected, findings, packages_count)

            has_vulns = any(f["severity"] != "NONE" for f in findings)

            while True:
                action_choices = []
                if has_vulns:
                    action_choices += [
                        "Show CRITICAL vulnerabilities only",
                        "Show HIGH vulnerabilities only",
                        "Show MEDIUM vulnerabilities only",
                        "Show LOW vulnerabilities only",
                    ]
                action_choices += [
                    "Export as PDF",
                    "Export as JSON",
                    "Scan another image",
                    "Quit",
                ]

                action = inquirer.select(
                    message="What do you want to do?",
                    choices=action_choices,
                    style=STYLE,
                    pointer="❯",
                ).execute()

                if action == "Show CRITICAL vulnerabilities only":
                    _show_results(selected, findings, packages_count, "CRITICAL")

                elif action == "Show HIGH vulnerabilities only":
                    _show_results(selected, findings, packages_count, "HIGH")

                elif action == "Show MEDIUM vulnerabilities only":
                    _show_results(selected, findings, packages_count, "MEDIUM")

                elif action == "Show LOW vulnerabilities only":
                    _show_results(selected, findings, packages_count, "LOW")

                elif action == "Export as PDF":
                    filename = inquirer.text(
                        message="PDF filename:", default="report.pdf", style=STYLE
                    ).execute()
                    export_pdf(selected, findings, filename)
                    console.print(f"[{ROSE}]PDF saved:[/{ROSE}] {filename}")

                elif action == "Export as JSON":
                    filename = inquirer.text(
                        message="JSON filename:", default="report.json", style=STYLE
                    ).execute()
                    with open(filename, "w") as f:
                        json.dump(
                            {"image": selected, "findings": findings}, f, indent=2
                        )
                    console.print(f"[{ROSE}]JSON saved:[/{ROSE}] {filename}")

                elif action == "Scan another image":
                    break

                elif action == "Quit":
                    console.print(f"\n[{ROSE}]Goodbye![/{ROSE}]")
                    return

    except KeyboardInterrupt:
        console.print(f"\n\n[{ROSE}]Interrupted. Goodbye![/{ROSE}]")
        sys.exit(0)
