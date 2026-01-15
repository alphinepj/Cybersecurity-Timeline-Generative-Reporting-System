"""
Full Pipeline Runner
--------------------
Runs the entire Cybersecurity Reporting System end-to-end.

Phase 1 → Phase 3.5 (PDF Export + Dashboard)
"""

import subprocess
import sys
from pathlib import Path


# =====================================================
# Paths
# =====================================================

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

PYTHON = sys.executable


# =====================================================
# Helpers
# =====================================================

def run(cmd: list, step: str):
    print(f"\n▶ {step}")
    print(" ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(f"❌ Failed at step: {step}")


def find_file(directory: Path, keywords: list):
    if not directory.exists():
        return None

    for file in directory.iterdir():
        if file.is_file():
            name = file.name.lower()
            if all(k.lower() in name for k in keywords):
                return file
    return None


# =====================================================
# Main Pipeline
# =====================================================

def run_pipeline(client: str, month: str):
    print(f"\n🚀 Running full pipeline for {client} — {month}")

    raw_dir = DATA / "raw" / month
    if not raw_dir.exists():
        sys.exit(f"❌ Raw data directory not found: {raw_dir}")

    # -------------------------
    # Phase 1 — Ingestion
    # -------------------------
    run(
        [PYTHON, str(SCRIPTS / "run_month.py"), "--month", month],
        "Phase 1: Ingestion & Normalization",
    )

    # -------------------------
    # Discover Reports
    # -------------------------
    edr_report = find_file(raw_dir, ["edr"])
    backup_report = find_file(raw_dir, ["backup"])
    phishing_report = find_file(raw_dir, ["phishing"])
    darkweb_report = find_file(raw_dir, ["dark", "web"])

    missing = [
        name for name, file in {
            "EDR": edr_report,
            "Backup": backup_report,
            "Phishing": phishing_report,
            "Dark Web": darkweb_report,
        }.items() if not file
    ]

    if missing:
        sys.exit(f"❌ Missing required report(s): {', '.join(missing)}")

    # -------------------------
    # Phase 2 — Enrichment
    # -------------------------
    run(
        [PYTHON, str(SCRIPTS / "enrichers/edr_enricher.py"),
         "--assets", f"data/normalized/{month}-assets.json",
         "--edr-report", str(edr_report),
         "--output", f"data/enriched/{month}-assets-edr.json"],
        "Phase 2.1: EDR Enrichment",
    )

    run(
        [PYTHON, str(SCRIPTS / "enrichers/backup_enricher.py"),
         "--assets", f"data/enriched/{month}-assets-edr.json",
         "--backup-report", str(backup_report),
         "--output", f"data/enriched/{month}-assets-edr-backup.json"],
        "Phase 2.2: Backup Enrichment",
    )

    run(
        [PYTHON, str(SCRIPTS / "enrichers/phishing_enricher.py"),
         "--users", f"data/normalized/{month}-users.json",
         "--phishing-report", str(phishing_report),
         "--output", f"data/enriched/{month}-users-phishing.json"],
        "Phase 2.3: Phishing Enrichment",
    )

    run(
        [PYTHON, str(SCRIPTS / "enrichers/darkweb_enricher.py"),
         "--users", f"data/enriched/{month}-users-phishing.json",
         "--darkweb-report", str(darkweb_report),
         "--output", f"data/enriched/{month}-users-phishing-darkweb.json"],
        "Phase 2.4: Dark Web Enrichment",
    )

    # -------------------------
    # Phase 2.5 — Insight Engine
    # -------------------------
    run(
        [PYTHON, str(SCRIPTS / "insight_engine.py"),
         "--users", f"data/enriched/{month}-users-phishing-darkweb.json",
         "--assets", f"data/enriched/{month}-assets-edr-backup.json",
         "--diff", f"data/diffs/{month}-diff.json",
         "--output", f"data/insights/{month}-insights.json"],
        "Phase 2.5: Insight Engine",
    )

    # -------------------------
    # Phase 2.6 — Narrative Builder
    # -------------------------
    run(
        [PYTHON, str(SCRIPTS / "narrative_builder.py"),
         "--insights", f"data/insights/{month}-insights.json",
         "--output", f"data/narratives/{month}-narrative.json"],
        "Phase 2.6: Narrative Builder",
    )

    # -------------------------
    # Phase 2.7 — Dashboard Aggregation ✅ FIXED
    # -------------------------
    run(
        [PYTHON, str(SCRIPTS / "dash_app/dashboard_aggregator.py"),
         "--client", client,
         "--month", month,
         "--insights", f"data/insights/{month}-insights.json",
         "--output", f"data/dashboard/{month}-dashboard.json"],
        "Phase 2.7: Dashboard Aggregation",
    )

    # -------------------------
    # Phase 3 — LLM Report
    # -------------------------
    run(
        [PYTHON, str(SCRIPTS / "llm/report_polisher.py"),
         "--narrative", f"data/narratives/{month}-narrative.json",
         "--output", f"reports/{month}/executive_report_polished.md"],
        "Phase 3: LLM-Polished Executive Report",
    )

    # -------------------------
    # Phase 3.5 — PDF Export
    # -------------------------
    run(
        [PYTHON, str(SCRIPTS / "exporters/pdf_exporter.py"),
         "--input", f"reports/{month}/executive_report_polished.md",
         "--output", f"reports/{month}/executive_report.pdf",
         "--client", client,
         "--month", month],
        "Phase 3.5: Executive PDF Export",
    )

    print("\n✅ FULL PIPELINE COMPLETED SUCCESSFULLY")
    print(f"📄 Markdown Report : reports/{month}/executive_report_polished.md")
    print(f"📄 PDF Report      : reports/{month}/executive_report.pdf")
    print(f"📊 Dashboard Data  : data/dashboard/{month}-dashboard.json")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run full cybersecurity reporting pipeline")
    parser.add_argument("--client", default="Altera Fund Advisors")
    parser.add_argument("--month", required=True)

    args = parser.parse_args()
    run_pipeline(client=args.client, month=args.month)
