# cli/output.py
# Display functions for DKLENS scan results.

import json

from rich.console import Console
from rich.table import Table
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus import Table as RLTable
from reportlab.platypus import TableStyle

console = Console()


def show_table(image: str, findings: list):
    table = Table(title=f"DKLENS Scan Report: {image}")
    table.add_column("Package")
    table.add_column("Version")
    table.add_column("Severity")
    table.add_column("CVE")
    table.add_column("EUVD ID")
    table.add_column("EUVD Score")
    table.add_column("Fix version")
    table.add_column("Command")
    table.add_column("Advisory")

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
            f.get("advisory_url") or "-",
        )

    console.print(table)


def show_json(image: str, findings: list):
    console.print_json(
        json.dumps(
            {
                "image": image,
                "findings": findings,
            }
        )
    )


ROSE = colors.HexColor("#785964")

SEVERITY_COLORS_PDF = {
    "CRITICAL": colors.HexColor("#FF0000"),
    "HIGH": colors.HexColor("#CC2200"),
    "MEDIUM": colors.HexColor("#FF8C00"),
    "LOW": colors.HexColor("#CCCC00"),
    "UNKNOWN": colors.HexColor("#888888"),
}


def export_pdf(image: str, findings: list, output_path: str):
    """Generate a PDF report of the scan results."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    story = []

    # Title in rose color
    title_style = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=ROSE,
        alignment=TA_CENTER,
    )
    story.append(Paragraph("DKLENS Scan Report", title_style))
    story.append(Spacer(1, 24))

    # Image info
    info_style = ParagraphStyle(
        "info",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.black,
        leading=14,
    )
    vuln_count = len([f for f in findings if f.get("severity", "NONE") != "NONE"])
    story.append(Paragraph(f"<b>Image:</b> {image}", info_style))
    story.append(Paragraph(f"<b>Vulnerabilities found:</b> {vuln_count}", info_style))
    story.append(Spacer(1, 10))

    # Paragraph styles for table cells (enables text wrapping)
    cell_style = ParagraphStyle("cell", fontName="Helvetica", fontSize=7, leading=9)

    # Table
    data = [["Package", "Version", "Severity", "CVE", "Fixed in", "Command"]]

    for f in findings:
        if f.get("severity") == "NONE":
            continue
        sev = f.get("severity", "UNKNOWN")
        sev_color = SEVERITY_COLORS_PDF.get(sev, colors.black)
        sev_style = ParagraphStyle(
            f"sev_{sev}",
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=sev_color,
        )
        data.append(
            [
                Paragraph(f.get("package") or "-", cell_style),
                Paragraph(f.get("version") or "-", cell_style),
                Paragraph(sev, sev_style),
                Paragraph(f.get("cve") or "-", cell_style),
                Paragraph(f.get("fix") or "-", cell_style),
                Paragraph(f.get("command") or "-", cell_style),
            ]
        )

    table = RLTable(data, colWidths=[75, 80, 55, 110, 70, 115])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ROSE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f5f0f1")],
                ),
                ("GRID", (0, 0), (-1, -1), 0.3, ROSE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)

    doc.build(story)
