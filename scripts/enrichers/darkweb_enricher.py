"""
Dark Web Enricher
----------------
Enriches existing user snapshots with dark web credential exposure data.

Phase: 2
Design:
- No new users created
- Email-based matching
- Safe enrichment only
"""

import json
import os
from datetime import datetime
from typing import Dict

import pdfplumber
import pandas as pd


# =====================================================
# Utilities
# =====================================================

def normalize_email(email: str) -> str:
    if not email:
        return ""
    return str(email).strip().lower()


def load_users(path: str) -> Dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Users file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def save_users(data: Dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# =====================================================
# Dark Web Parsing (PDF)
# =====================================================

def parse_darkweb_pdf(path: str) -> Dict[str, dict]:
    """
    Parses Dark Web PDF reports and returns:
    {
      email: {
        exposed: True,
        source: "breach source",
        severity: "low|medium|high"
      }
    }
    """

    darkweb_data = {}

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table or len(table) < 2:
                continue

            headers = [str(h).strip().lower() for h in table[0]]

            for row in table[1:]:
                data = dict(zip(headers, row))

                email = normalize_email(
                    data.get("email")
                    or data.get("email address")
                    or data.get("user")
                    or ""
                )

                if not email:
                    continue

                source = (
                    str(data.get("breach source", "")).strip()
                    or str(data.get("source", "")).strip()
                    or "unknown"
                )

                severity_raw = str(data.get("severity", "")).lower()

                if "high" in severity_raw:
                    severity = "high"
                elif "medium" in severity_raw:
                    severity = "medium"
                else:
                    severity = "low"

                darkweb_data[email] = {
                    "exposed": True,
                    "source": source,
                    "severity": severity
                }

    return darkweb_data


# =====================================================
# Enrichment Logic
# =====================================================

def enrich_users_with_darkweb(users: Dict, darkweb_data: Dict):
    """
    Merges dark web exposure data into existing users
    """

    for email, user in users["users"].items():

        exposure = darkweb_data.get(email)

        if exposure:
            user["risk_signals"]["dark_web_exposed"] = True
            user["risk_signals"]["dark_web_source"] = exposure["source"]
            user["risk_signals"]["dark_web_severity"] = exposure["severity"]

        else:
            user["risk_signals"]["dark_web_exposed"] = False
            user["risk_signals"]["dark_web_severity"] = "none"


# =====================================================
# Main Orchestrator
# =====================================================

def run_darkweb_enrichment(
    user_snapshot_path: str,
    darkweb_report_path: str,
    output_path: str
):
    users = load_users(user_snapshot_path)
    darkweb_data = parse_darkweb_pdf(darkweb_report_path)

    enrich_users_with_darkweb(users, darkweb_data)

    users["metadata"]["darkweb_enriched_at"] = datetime.utcnow().isoformat() + "Z"

    save_users(users, output_path)

    print("✅ Dark Web enrichment completed")
    print(f"📄 Enriched user file written to: {output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dark Web Enricher")
    parser.add_argument("--users", required=True, help="Path to user snapshot JSON")
    parser.add_argument("--darkweb-report", required=True, help="Path to Dark Web PDF report")
    parser.add_argument("--output", required=True, help="Output enriched user JSON")

    args = parser.parse_args()

    run_darkweb_enrichment(
        user_snapshot_path=args.users,
        darkweb_report_path=args.darkweb_report,
        output_path=args.output
    )
