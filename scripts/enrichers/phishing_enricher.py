"""
Phishing Enricher
-----------------
Enriches existing user snapshots with phishing simulation data.

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
# Phishing Parsing (PDF)
# =====================================================

def parse_phishing_pdf(path: str) -> Dict[str, dict]:
    """
    Parses Phishing PDF reports and returns:
    {
      email: {
        sent: int,
        clicked: int
      }
    }
    """

    phishing_data = {}

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
                    or data.get("user")
                    or data.get("email address")
                    or ""
                )

                if not email:
                    continue

                sent = int(data.get("emails sent", 1) or 1)
                clicked = int(data.get("clicked", 0) or 0)

                phishing_data[email] = {
                    "sent": sent,
                    "clicked": clicked
                }

    return phishing_data


# =====================================================
# Enrichment Logic
# =====================================================

def enrich_users_with_phishing(users: Dict, phishing_data: Dict):
    """
    Merges phishing data into existing users
    """

    for email, user in users["users"].items():

        phishing = phishing_data.get(email)

        if phishing:
            user["risk_signals"]["phishing_clicked"] = phishing["clicked"] > 0
            user["risk_signals"]["phishing_failures"] = phishing["clicked"]
            user["risk_signals"]["phishing_campaigns"] = phishing["sent"]

            if phishing["clicked"] > 0:
                user["risk_signals"]["phishing_risk"] = "high"
            else:
                user["risk_signals"]["phishing_risk"] = "low"

        else:
            user["risk_signals"]["phishing_campaigns"] = 0
            user["risk_signals"]["phishing_failures"] = 0
            user["risk_signals"]["phishing_risk"] = "unknown"


# =====================================================
# Main Orchestrator
# =====================================================

def run_phishing_enrichment(
    user_snapshot_path: str,
    phishing_report_path: str,
    output_path: str
):
    users = load_users(user_snapshot_path)
    phishing_data = parse_phishing_pdf(phishing_report_path)

    enrich_users_with_phishing(users, phishing_data)

    users["metadata"]["phishing_enriched_at"] = datetime.utcnow().isoformat() + "Z"

    save_users(users, output_path)

    print("✅ Phishing enrichment completed")
    print(f"📄 Enriched user file written to: {output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phishing Enricher")
    parser.add_argument("--users", required=True, help="Path to user snapshot JSON")
    parser.add_argument("--phishing-report", required=True, help="Path to Phishing PDF report")
    parser.add_argument("--output", required=True, help="Output enriched user JSON")

    args = parser.parse_args()

    run_phishing_enrichment(
        user_snapshot_path=args.users,
        phishing_report_path=args.phishing_report,
        output_path=args.output
    )
