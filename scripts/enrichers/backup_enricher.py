"""
Backup Enricher
---------------
Enriches existing asset snapshots with Backup health data.

Phase: 2
Design:
- No new assets created
- Serial-number–based matching
- Safe enrichment only
"""

import json
import os
from datetime import datetime
from typing import Dict

import pandas as pd
import pdfplumber


# =====================================================
# Utilities
# =====================================================

def normalize_serial(serial: str) -> str:
    if not serial:
        return ""
    return str(serial).strip().upper()


def load_assets(path: str) -> Dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Assets file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def save_assets(data: Dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# =====================================================
# Backup Parsing (PDF)
# =====================================================

def parse_backup_pdf(path: str) -> Dict[str, dict]:
    """
    Parses Backup PDF reports and returns:
    {
      SERIAL: {
        status: "healthy" | "failed" | "in_progress",
        last_success: "YYYY-MM-DD"
      }
    }
    """

    backup_data = {}

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table or len(table) < 2:
                continue

            headers = [str(h).strip().lower() for h in table[0]]

            for row in table[1:]:
                data = dict(zip(headers, row))

                serial = normalize_serial(
                    data.get("serial number")
                    or data.get("serial")
                    or ""
                )

                if not serial:
                    continue

                status_raw = str(data.get("status", "")).lower()

                if "success" in status_raw or "completed" in status_raw:
                    status = "healthy"
                elif "fail" in status_raw:
                    status = "failed"
                elif "progress" in status_raw:
                    status = "in_progress"
                else:
                    status = "unknown"

                last_success = (
                    str(data.get("last successful backup", "")).strip()
                    or None
                )

                backup_data[serial] = {
                    "status": status,
                    "last_success": last_success
                }

    return backup_data


# =====================================================
# Enrichment Logic
# =====================================================

def enrich_assets_with_backup(assets: Dict, backup_data: Dict):
    """
    Merges Backup data into existing assets
    """

    for asset_id, asset in assets["assets"].items():

        serial = normalize_serial(asset.get("serial_number", ""))

        if not serial:
            continue

        backup = backup_data.get(serial)

        if "backup_state" not in asset:
            asset["backup_state"] = {}

        if backup:
            asset["backup_state"]["enabled"] = True
            asset["backup_state"]["status"] = backup["status"]
            asset["backup_state"]["last_success"] = backup["last_success"]

            if backup["status"] == "failed":
                asset["backup_state"]["risk_level"] = "critical"
            elif backup["status"] == "in_progress":
                asset["backup_state"]["risk_level"] = "medium"
            else:
                asset["backup_state"]["risk_level"] = "low"

        else:
            asset["backup_state"]["enabled"] = False
            asset["backup_state"]["status"] = "not_configured"
            asset["backup_state"]["risk_level"] = "high"


# =====================================================
# Main Orchestrator
# =====================================================

def run_backup_enrichment(
    asset_snapshot_path: str,
    backup_report_path: str,
    output_path: str
):
    assets = load_assets(asset_snapshot_path)
    backup_data = parse_backup_pdf(backup_report_path)

    enrich_assets_with_backup(assets, backup_data)

    assets["metadata"]["backup_enriched_at"] = datetime.utcnow().isoformat() + "Z"

    save_assets(assets, output_path)

    print("✅ Backup enrichment completed")
    print(f"📄 Enriched asset file written to: {output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backup Enricher")
    parser.add_argument("--assets", required=True, help="Path to asset snapshot JSON")
    parser.add_argument("--backup-report", required=True, help="Path to Backup PDF report")
    parser.add_argument("--output", required=True, help="Output enriched asset JSON")

    args = parser.parse_args()

    run_backup_enrichment(
        asset_snapshot_path=args.assets,
        backup_report_path=args.backup_report,
        output_path=args.output
    )
