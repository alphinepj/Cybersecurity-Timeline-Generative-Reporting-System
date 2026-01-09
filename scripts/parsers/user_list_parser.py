"""
User List Parser
----------------
Parses User List reports (PDF / XLSX) into canonical JSON user objects.

Phase: 1 (DB-less)
"""

import json
import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
import pdfplumber


# =========================
# Column Synonyms
# =========================

EMAIL_COLUMNS = [
    "email",
    "email address",
    "user principal name",
    "upn",
    "login",
    "login name",
    "username"
]

FIRST_NAME_COLUMNS = [
    "first name",
    "firstname",
    "given name"
]

LAST_NAME_COLUMNS = [
    "last name",
    "lastname",
    "surname"
]

NAME_COLUMNS = [
    "name",
    "full name",
    "display name"
]

STATUS_COLUMNS = [
    "status",
    "account status",
    "enabled",
    "active",
    "sign-in allowed"
]

PRODUCT_COLUMNS = [
    "microsoft 365 assigned products",
    "assigned products",
    "licenses",
    "products"
]


# =========================
# Utility Functions
# =========================

def normalize_email(email: str) -> str:
    if not email:
        return ""
    return email.strip().lower()


def normalize_col(col) -> str:
    if not col:
        return ""
    return str(col).lower().strip()


def month_to_str(month: str) -> str:
    datetime.strptime(month, "%Y-%m")
    return month


def load_previous_snapshot(path: str) -> Dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("users", {})


def find_column(df: pd.DataFrame, candidates: List[str]):
    for col in df.columns:
        if normalize_col(col) in candidates:
            return col
    return None


# =========================
# User Builder
# =========================

def build_user(email, name, status_raw, products_raw, month):
    status_raw = (status_raw or "").lower()

    return {
        "name": name or email.split("@")[0],
        "status": "active" if status_raw in ("yes", "true", "enabled", "active", "1") else "inactive",
        "first_seen": None,
        "last_seen": month,
        "services": {
            "m365": any(
                k in (products_raw or "").lower()
                for k in ("office 365", "microsoft 365", "m365")
            ),
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


# =========================
# Excel Parser
# =========================

def parse_user_list_xlsx(path: str, month: str) -> Dict[str, dict]:
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]

    email_col = find_column(df, EMAIL_COLUMNS)
    if not email_col:
        raise ValueError(f"❌ No email column found. Columns: {list(df.columns)}")

    first_col = find_column(df, FIRST_NAME_COLUMNS)
    last_col = find_column(df, LAST_NAME_COLUMNS)
    name_col = find_column(df, NAME_COLUMNS)
    status_col = find_column(df, STATUS_COLUMNS)
    product_col = find_column(df, PRODUCT_COLUMNS)

    users = {}

    for _, row in df.iterrows():
        raw_email = str(row.get(email_col, "")).strip()
        if "@" not in raw_email:
            continue

        email = normalize_email(raw_email)

        if name_col:
            name = str(row.get(name_col, "")).strip()
        else:
            first = str(row.get(first_col, "")).strip() if first_col else ""
            last = str(row.get(last_col, "")).strip() if last_col else ""
            name = f"{first} {last}".strip()

        users[email] = build_user(
            email,
            name,
            row.get(status_col, "active") if status_col else "active",
            row.get(product_col, "") if product_col else "",
            month
        )

    if not users:
        raise ValueError("❌ Parsed 0 users from XLSX")

    return users


# =========================
# PDF Parser (HARDENED)
# =========================

def parse_user_list_pdf(path: str, month: str) -> Dict[str, dict]:
    users = {}

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table or len(table) < 2:
                continue

            header_row_index = None

            # Detect real header row
            for i, row in enumerate(table):
                if not row:
                    continue

                cells = [str(c).lower() for c in row if c]
                if len(row) >= 6 and any("email" in c for c in cells):
                    header_row_index = i
                    break

            if header_row_index is None:
                continue

            raw_headers = table[header_row_index]

            headers = [
                normalize_col(h) if h else f"col_{i}"
                for i, h in enumerate(raw_headers)
            ]

            data_rows = [
                r for r in table[header_row_index + 1 :]
                if r and len(r) == len(headers)
            ]

            if not data_rows:
                continue

            df = pd.DataFrame(data_rows, columns=headers)

            email_col = find_column(df, EMAIL_COLUMNS)
            if not email_col:
                continue

            first_col = find_column(df, FIRST_NAME_COLUMNS)
            last_col = find_column(df, LAST_NAME_COLUMNS)
            name_col = find_column(df, NAME_COLUMNS)
            status_col = find_column(df, STATUS_COLUMNS)
            product_col = find_column(df, PRODUCT_COLUMNS)

            for _, row in df.iterrows():
                raw_email = str(row.get(email_col, "")).strip()
                if "@" not in raw_email:
                    continue

                email = normalize_email(raw_email)

                if name_col:
                    name = str(row.get(name_col, "")).strip()
                else:
                    first = str(row.get(first_col, "")).strip() if first_col else ""
                    last = str(row.get(last_col, "")).strip() if last_col else ""
                    name = f"{first} {last}".strip()

                users[email] = build_user(
                    email,
                    name,
                    row.get(status_col, "active") if status_col else "active",
                    row.get(product_col, "") if product_col else "",
                    month
                )

    if not users:
        raise ValueError("❌ Parsed 0 users from PDF")

    return users


# =========================
# First Seen Resolution
# =========================

def resolve_first_seen(current: Dict, previous: Dict, month: str):
    for email, user in current.items():
        user["first_seen"] = previous.get(email, {}).get("first_seen", month)


# =========================
# Validation
# =========================

def validate_users(users: Dict):
    if not users:
        raise ValueError("❌ No users parsed")

    for email, user in users.items():
        if not user.get("name"):
            raise ValueError(f"User missing name: {email}")
        if not user.get("first_seen"):
            raise ValueError(f"User missing first_seen: {email}")


# =========================
# Main Orchestrator
# =========================

def parse_user_list(input_path, month, previous_snapshot_path, output_path):
    month = month_to_str(month)
    previous_users = load_previous_snapshot(previous_snapshot_path)

    if input_path.lower().endswith(".xlsx"):
        current_users = parse_user_list_xlsx(input_path, month)
    elif input_path.lower().endswith(".pdf"):
        current_users = parse_user_list_pdf(input_path, month)
    else:
        raise ValueError("Unsupported file type")

    resolve_first_seen(current_users, previous_users, month)
    validate_users(current_users)

    snapshot = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "month": month,
            "source": "user_list"
        },
        "users": current_users
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    print(f"✅ User list parsed successfully: {len(current_users)} users")
    print(f"📄 Output written to: {output_path}")


# =========================
# CLI
# =========================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="User List Parser")
    parser.add_argument("--input", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--previous", default="")
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    parse_user_list(
        input_path=args.input,
        month=args.month,
        previous_snapshot_path=args.previous,
        output_path=args.output
    )
