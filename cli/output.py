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
    console.print_json(json.dumps({
        "image": image,
        "findings": findings,
    }))


from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def export_pdf(image: str, findings: list, output_path: str):
    """Generate a PDF report of the scan results."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"DockLens Scan Report", styles['Title']))
    story.append(Paragraph(f"Image: {image}", styles['Normal']))
    story.append(Spacer(1, 12))

    data = [["Package", "Version", "Severity", "CVE", "Fix", "Command"]]
    for f in findings:
        data.append([
            f["package"],
            f["version"] or "-",
            f["severity"],
            f.get("cve") or "-",
            f.get("fix") or "-",
            f.get("command") or "-",
        ])

    table = RLTable(data, colWidths=[80, 70, 60, 120, 70, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#16213e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f4ff')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(table)
    doc.build(story)
