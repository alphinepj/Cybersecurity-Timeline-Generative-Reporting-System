"""
User List Parser
----------------
Parses User List reports (PDF / XLSX) into canonical JSON user objects.

Author: Cyber Timeline System
Phase: 1 (DB-less)
"""

import json
import os
from datetime import datetime
from typing import Dict

import pandas as pd
import pdfplumber


# =========================
# Utility Functions
# =========================

def normalize_email(email: str) -> str:
    if not email:
        return ""
    return email.strip().lower()


def month_to_str(month: str) -> str:
    """
    Ensures month format YYYY-MM
    """
    try:
        datetime.strptime(month, "%Y-%m")
        return month
    except ValueError:
        raise ValueError("Month must be in YYYY-MM format")


def load_previous_snapshot(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f).get("users", {})


# =========================
# Excel Parser
# =========================

def parse_user_list_xlsx(path: str, month: str) -> Dict[str, dict]:
    df = pd.read_excel(path)
    users = {}

    for _, row in df.iterrows():
        email = normalize_email(str(row.get("Email Address", "")))
        if not email or email == "nan":
            continue

        first = str(row.get("First Name", "")).strip()
        last = str(row.get("Last Name", "")).strip()
        sign_in = str(row.get("Sign-in Allowed", "")).strip().lower()
        products = str(row.get("Microsoft 365 Assigned Products", ""))

        users[email] = {
            "name": f"{first} {last}".strip(),
            "status": "active" if sign_in == "yes" else "inactive",
            "first_seen": None,  # resolved later
            "last_seen": month,
            "services": {
                "m365": "office 365" in products.lower() or "microsoft 365" in products.lower(),
                "edr": False,
                "backup": False,
                "phishing_training": False,
                "dark_web_monitoring": False
            },
            "risk_signals": {
                "phishing_clicked": False,
                "dark_web_exposed": False,
                "edr_incidents": 0
            }
        }

    return users


# =========================
# PDF Parser
# =========================

def parse_user_list_pdf(path: str, month: str) -> Dict[str, dict]:
    users = {}

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table or len(table) < 2:
                continue

            headers = [h.strip() if h else "" for h in table[0]]

            for row in table[1:]:
                data = dict(zip(headers, row))
                email = normalize_email(data.get("Email Address", ""))

                if not email:
                    continue

                products = str(data.get("Microsoft 365 Assigned Products", ""))

                users[email] = {
                    "name": f"{data.get('First Name','')} {data.get('Last Name','')}".strip(),
                    "status": "active" if str(data.get("Sign-in Allowed", "")).lower() == "yes" else "inactive",
                    "first_seen": None,
                    "last_seen": month,
                    "services": {
                        "m365": "office 365" in products.lower() or "microsoft 365" in products.lower(),
                        "edr": False,
                        "backup": False,
                        "phishing_training": False,
                        "dark_web_monitoring": False
                    },
                    "risk_signals": {
                        "phishing_clicked": False,
                        "dark_web_exposed": False,
                        "edr_incidents": 0
                    }
                }

    return users


# =========================
# First-Seen Resolution
# =========================

def resolve_first_seen(current: Dict, previous: Dict, month: str):
    for email, user in current.items():
        if email in previous:
            user["first_seen"] = previous[email].get("first_seen")
        else:
            user["first_seen"] = month


# =========================
# Validation
# =========================

def validate_users(users: Dict):
    emails = set()
    for email, user in users.items():
        if email in emails:
            raise ValueError(f"Duplicate user detected: {email}")
        emails.add(email)

        if not user["name"]:
            raise ValueError(f"User missing name: {email}")

        if not user["first_seen"]:
            raise ValueError(f"User missing first_seen: {email}")


# =========================
# Main Orchestrator
# =========================

def parse_user_list(
    input_path: str,
    month: str,
    previous_snapshot_path: str,
    output_path: str
):
    month = month_to_str(month)

    # Load previous users (if any)
    previous_users = load_previous_snapshot(previous_snapshot_path)

    # Parse input
    if input_path.lower().endswith(".xlsx"):
        current_users = parse_user_list_xlsx(input_path, month)
    elif input_path.lower().endswith(".pdf"):
        current_users = parse_user_list_pdf(input_path, month)
    else:
        raise ValueError("Unsupported file format (use .pdf or .xlsx)")

    # Resolve first_seen
    resolve_first_seen(current_users, previous_users, month)

    # Validation
    validate_users(current_users)

    # Build output snapshot
    snapshot = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "month": month,
            "source": "user_list"
        },
        "users": current_users
    }

    # Ensure output dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"✅ User list parsed successfully: {len(current_users)} users")
    print(f"📄 Output written to: {output_path}")


# =========================
# CLI Usage
# =========================

if __name__ == "__main__":
    """
    Example:
    python user_list_parser.py \
      --input data/raw/2025-11/user_list.xlsx \
      --month 2025-11 \
      --previous data/normalized/2025-10.json \
      --output data/normalized/2025-11.json
    """

    import argparse

    parser = argparse.ArgumentParser(description="User List Parser")
    parser.add_argument("--input", required=True, help="Path to user list PDF/XLSX")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM")
    parser.add_argument("--previous", required=False, default="", help="Previous month snapshot JSON")
    parser.add_argument("--output", required=True, help="Output normalized JSON path")

    args = parser.parse_args()

    parse_user_list(
        input_path=args.input,
        month=args.month,
        previous_snapshot_path=args.previous,
        output_path=args.output
    )
