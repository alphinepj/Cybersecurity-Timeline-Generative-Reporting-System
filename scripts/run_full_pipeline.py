"""
Full Pipeline Runner
--------------------
Runs the entire Cybersecurity Reporting System end-to-end.

Phase 1 → Phase 3
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
    """
    Finds the first file whose name contains ALL keywords.
    Matching is case-insensitive.
    """
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
    # Phase 1 — Monthly Runner
    # -------------------------
    run(
        [
            PYTHON,
            str(SCRIPTS / "run_month.py"),
            "--month",
            month,
        ],
        "Phase 1: Ingestion & Normalization",
    )

    # -------------------------
    # Discover Reports (INTENT-BASED)
    # -------------------------

    edr_report = (
        find_file(raw_dir, ["edr"]) or
        find_file(raw_dir, ["rocket", "cyber"])
    )

    backup_report = (
        find_file(raw_dir, ["backup"]) or
        find_file(raw_dir, ["files", "folders"]) or
        find_file(raw_dir, ["file", "folder"])
    )

    phishing_report = find_file(raw_dir, ["phishing"])

    darkweb_report = (
        find_file(raw_dir, ["dark", "web"]) or
        find_file(raw_dir, ["darkweb"])
    )

    # -------------------------
    # Validation
    # -------------------------

    missing = []
    if not edr_report:
        missing.append("EDR")
    if not backup_report:
        missing.append("Backup")
    if not phishing_report:
        missing.append("Phishing")
    if not darkweb_report:
        missing.append("Dark Web")

    if missing:
        print("\n📂 Files present in raw folder:")
        for f in raw_dir.iterdir():
            print(f"   - {f.name}")
        sys.exit(f"\n❌ Missing required report(s): {', '.join(missing)}")

    print("\n📄 Discovered reports:")
    print(f"   • EDR     : {edr_report.name}")
    print(f"   • Backup  : {backup_report.name}")
    print(f"   • Phishing: {phishing_report.name}")
    print(f"   • DarkWeb : {darkweb_report.name}")

    # -------------------------
    # Phase 2 — Enrichers
    # -------------------------

    run(
        [
            PYTHON,
            str(SCRIPTS / "enrichers/edr_enricher.py"),
            "--assets",
            f"data/normalized/{month}-assets.json",
            "--edr-report",
            str(edr_report),
            "--output",
            f"data/enriched/{month}-assets-edr.json",
        ],
        "Phase 2.1: EDR Enrichment",
    )

    run(
        [
            PYTHON,
            str(SCRIPTS / "enrichers/backup_enricher.py"),
            "--assets",
            f"data/enriched/{month}-assets-edr.json",
            "--backup-report",
            str(backup_report),
            "--output",
            f"data/enriched/{month}-assets-edr-backup.json",
        ],
        "Phase 2.2: Backup Enrichment",
    )

    run(
        [
            PYTHON,
            str(SCRIPTS / "enrichers/phishing_enricher.py"),
            "--users",
            f"data/normalized/{month}-users.json",
            "--phishing-report",
            str(phishing_report),
            "--output",
            f"data/enriched/{month}-users-phishing.json",
        ],
        "Phase 2.3: Phishing Enrichment",
    )

    run(
        [
            PYTHON,
            str(SCRIPTS / "enrichers/darkweb_enricher.py"),
            "--users",
            f"data/enriched/{month}-users-phishing.json",
            "--darkweb-report",
            str(darkweb_report),
            "--output",
            f"data/enriched/{month}-users-phishing-darkweb.json",
        ],
        "Phase 2.4: Dark Web Enrichment",
    )

    # -------------------------
    # Phase 2.5 — Insights
    # -------------------------

    run(
        [
            PYTHON,
            str(SCRIPTS / "insight_engine.py"),
            "--users",
            f"data/enriched/{month}-users-phishing-darkweb.json",
            "--assets",
            f"data/enriched/{month}-assets-edr-backup.json",
            "--diff",
            f"data/diffs/{month}-diff.json",
            "--output",
            f"data/insights/{month}-insights.json",
        ],
        "Phase 2.5: Insight Engine",
    )

    # -------------------------
    # Phase 2.6 — Narrative
    # -------------------------

    run(
        [
            PYTHON,
            str(SCRIPTS / "narrative_builder.py"),
            "--insights",
            f"data/insights/{month}-insights.json",
            "--output",
            f"data/narratives/{month}-narrative.json",
        ],
        "Phase 2.6: Narrative Builder",
    )

    # -------------------------
    # Phase 3 — LLM Polishing (FLAN)
    # -------------------------

    run(
        [
            PYTHON,
            str(SCRIPTS / "llm/report_polisher.py"),
            "--narrative",
            f"data/narratives/{month}-narrative.json",
            "--output",
            f"reports/{month}/executive_report_polished.md",
        ],
        "Phase 3: LLM-Polished Executive Report",
    )

    print("\n✅ FULL PIPELINE COMPLETED SUCCESSFULLY")
    print(f"📄 Final report: reports/{month}/executive_report_polished.md")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run full cybersecurity reporting pipeline"
    )
    parser.add_argument(
        "--client",
        default="altera",
        help="Client identifier (future use)"
    )
    parser.add_argument(
        "--month",
        required=True,
        help="Month in YYYY-MM format"
    )

    args = parser.parse_args()

    run_pipeline(client=args.client, month=args.month)
