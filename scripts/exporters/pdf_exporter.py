"""
PDF Exporter
------------
Converts a polished executive Markdown report into a professional PDF.

Phase: 3.5
Design:
- Deterministic
- No LLM
- Executive-ready formatting
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.units import inch
import markdown2


# =====================================================
# Helpers
# =====================================================

def ensure_file(path: str):
    if not os.path.exists(path):
        sys.exit(f"❌ File not found: {path}")


def header_footer(canvas, doc):
    canvas.saveState()

    # Footer
    canvas.setFont("Helvetica", 9)
    footer_text = (
        "Confidential — Executive Security Report | "
        f"Generated {datetime.utcnow().strftime('%Y-%m-%d')}"
    )
    canvas.drawCentredString(LETTER[0] / 2, 0.5 * inch, footer_text)

    # Page number
    canvas.drawRightString(
        LETTER[0] - 0.75 * inch,
        0.5 * inch,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# =====================================================
# Main Exporter
# =====================================================

def export_pdf(markdown_path: str, output_pdf_path: str, client: str, month: str):
    ensure_file(markdown_path)
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    # -------------------------
    # Load Markdown
    # -------------------------
    with open(markdown_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    html = markdown2.markdown(md_text)

    # -------------------------
    # PDF Setup
    # -------------------------
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=LETTER,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="TitleStyle",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=24,
            spaceBefore=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            fontSize=14,
            leading=18,
            spaceBefore=18,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextExec",
            fontSize=11,
            leading=15,
            spaceAfter=10,
        )
    )

    # -------------------------
    # Build Document
    # -------------------------
    elements = []

    # Title Page
    elements.append(Spacer(1, 1.5 * inch))
    elements.append(Paragraph("Executive Security Report", styles["TitleStyle"]))
    elements.append(Paragraph(f"Client: {client}", styles["BodyTextExec"]))
    elements.append(Paragraph(f"Reporting Period: {month}", styles["BodyTextExec"]))
    elements.append(PageBreak())

    # -------------------------
    # Parse Markdown Sections
    # -------------------------
    for block in html.split("<h2>"):
        if "</h2>" in block:
            header, body = block.split("</h2>", 1)
            header_text = header.replace("<h2>", "").strip()

            elements.append(Paragraph(header_text, styles["SectionHeader"]))

            body = body.replace("<p>", "").replace("</p>", "\n").strip()
            for para in body.split("\n"):
                if para.strip():
                    elements.append(
                        Paragraph(para.strip(), styles["BodyTextExec"])
                    )
        else:
            body = block.replace("<p>", "").replace("</p>", "\n").strip()
            for para in body.split("\n"):
                if para.strip():
                    elements.append(
                        Paragraph(para.strip(), styles["BodyTextExec"])
                    )

    # -------------------------
    # Build PDF
    # -------------------------
    doc.build(
        elements,
        onFirstPage=header_footer,
        onLaterPages=header_footer
    )

    print("✅ Executive PDF generated")
    print(f"📄 PDF saved to: {os.path.abspath(output_pdf_path)}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Executive PDF Exporter")
    parser.add_argument("--input", required=True, help="Executive report Markdown file")
    parser.add_argument("--output", required=True, help="Output PDF file")
    parser.add_argument("--client", required=True, help="Client name")
    parser.add_argument("--month", required=True, help="Reporting month YYYY-MM")

    args = parser.parse_args()

    export_pdf(
        markdown_path=args.input,
        output_pdf_path=args.output,
        client=args.client,
        month=args.month
    )
