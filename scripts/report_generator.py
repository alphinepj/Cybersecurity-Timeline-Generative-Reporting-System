"""
Report Generator
----------------
Converts structured narrative JSON into an executive-ready Markdown report.

Phase: 2
Design:
- Deterministic
- Print-ready
- AI-optional
"""

import json
import os
from datetime import datetime
from typing import Dict


# =====================================================
# Load / Save
# =====================================================

def load_json(path: str) -> Dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def save_text(content: str, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


# =====================================================
# Markdown Builders
# =====================================================

def build_markdown_report(narrative: Dict, title: str, period: str) -> str:
    lines = []

    # ---- Title ----
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Reporting Period:** {period}")
    lines.append(f"**Generated On:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ---- Executive Summary ----
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(narrative.get("executive_summary", "No summary available."))
    lines.append("")

    # ---- Identity Changes ----
    identity = narrative.get("identity_changes", [])
    if identity:
        lines.append("## Identity Changes")
        lines.append("")
        for item in identity:
            lines.append(f"- {item}")
        lines.append("")

    # ---- Asset Changes ----
    assets = narrative.get("asset_changes", [])
    if assets:
        lines.append("## Asset Changes")
        lines.append("")
        for item in assets:
            lines.append(f"- {item}")
        lines.append("")

    # ---- Security Findings ----
    risks = narrative.get("security_findings", [])
    lines.append("## Security Findings")
    lines.append("")
    if risks:
        for item in risks:
            lines.append(f"- ⚠️ {item}")
    else:
        lines.append("No critical or high-risk security findings were identified.")
    lines.append("")

    # ---- Positive Observations ----
    positives = narrative.get("positive_observations", [])
    if positives:
        lines.append("## Positive Observations")
        lines.append("")
        for item in positives:
            lines.append(f"- ✅ {item}")
        lines.append("")

    # ---- Footer ----
    lines.append("---")
    lines.append("")
    lines.append(
        "_This report is generated automatically from verified security telemetry "
        "and is intended for executive and audit review._"
    )

    return "\n".join(lines)


# =====================================================
# Main Orchestrator
# =====================================================

def generate_report(
    narrative_path: str,
    output_path: str,
    title: str,
    period: str
):
    narrative = load_json(narrative_path)

    report_md = build_markdown_report(
        narrative=narrative,
        title=title,
        period=period
    )

    save_text(report_md, output_path)

    print("✅ Report generated successfully")
    print(f"📄 Report written to: {output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Executive Report Generator")
    parser.add_argument("--narrative", required=True, help="Path to narrative JSON")
    parser.add_argument("--output", required=True, help="Output Markdown report")
    parser.add_argument("--title", required=True, help="Report title")
    parser.add_argument("--period", required=True, help="Reporting period (e.g. October 2025)")

    args = parser.parse_args()

    generate_report(
        narrative_path=args.narrative,
        output_path=args.output,
        title=args.title,
        period=args.period
    )
