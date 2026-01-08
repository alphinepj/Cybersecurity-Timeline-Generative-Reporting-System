"""
EDR Enricher
------------
Enriches existing asset snapshots with EDR (Endpoint Detection & Response) data.

Phase: 2
Design:
- No new assets created
- Serial-number–based asset matching
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
# EDR Parsing (PDF)
# =====================================================

def parse_edr_pdf(path: str) -> Dict[str, dict]:
    """
    Parses EDR PDF reports and returns:
    {
      SERIAL: {
        alerts: int,
        incidents: int
      }
    }
    """

    edr_data = {}

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

                alerts = int(data.get("alerts", 0) or 0)
                incidents = int(data.get("incidents", 0) or 0)

                edr_data[serial] = {
                    "alerts": alerts,
                    "incidents": incidents
                }

    return edr_data


# =====================================================
# Enrichment Logic
# =====================================================

def enrich_assets_with_edr(assets: Dict, edr_data: Dict):
    """
    Merges EDR data into existing assets
    """

    for asset_id, asset in assets["assets"].items():

        serial = normalize_serial(asset.get("serial_number", ""))

        if not serial:
            continue

        edr = edr_data.get(serial)

        if edr:
            asset["security_state"]["edr_installed"] = True
            asset["security_state"]["edr_alerts"] = edr["alerts"]
            asset["security_state"]["edr_incidents"] = edr["incidents"]

            if edr["incidents"] > 0:
                asset["security_state"]["risk_level"] = "high"
            elif edr["alerts"] > 0:
                asset["security_state"]["risk_level"] = "medium"
            else:
                asset["security_state"]["risk_level"] = "low"

        else:
            asset["security_state"]["edr_installed"] = False
            asset["security_state"]["risk_level"] = "unknown"


# =====================================================
# Main Orchestrator
# =====================================================

def run_edr_enrichment(
    asset_snapshot_path: str,
    edr_report_path: str,
    output_path: str
):
    assets = load_assets(asset_snapshot_path)
    edr_data = parse_edr_pdf(edr_report_path)

    enrich_assets_with_edr(assets, edr_data)

    assets["metadata"]["edr_enriched_at"] = datetime.utcnow().isoformat() + "Z"

    save_assets(assets, output_path)

    print("✅ EDR enrichment completed")
    print(f"📄 Enriched asset file written to: {output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EDR Enricher")
    parser.add_argument("--assets", required=True, help="Path to asset snapshot JSON")
    parser.add_argument("--edr-report", required=True, help="Path to EDR PDF report")
    parser.add_argument("--output", required=True, help="Output enriched asset JSON")

    args = parser.parse_args()

    run_edr_enrichment(
        asset_snapshot_path=args.assets,
        edr_report_path=args.edr_report,
        output_path=args.output
    )
