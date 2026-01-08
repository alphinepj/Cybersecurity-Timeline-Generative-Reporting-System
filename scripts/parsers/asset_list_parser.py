"""
Asset List Parser (Serial-Based IDs)
-----------------------------------
Parses Asset List reports (PDF / XLSX) into canonical JSON asset objects.

Key Design:
- Asset ID = Serial Number (preferred)
- Fallback = Device Name (only if serial missing)
- Handles messy Excel exports (titles, merged headers, fuzzy columns)
- Logs skipped rows & duplicates
- DB-less, deterministic, audit-safe

Phase: 1
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

def normalize_device_name(name: str) -> str:
    if not name:
        return ""
    return str(name).strip().upper()


def normalize_serial(serial: str) -> str:
    if not serial:
        return ""
    return str(serial).strip().upper()


def normalize_email(email: str) -> str:
    if not email:
        return ""
    return str(email).strip().lower()


def generate_asset_id(device_name: str, serial: str) -> str:
    """
    Asset identity rule:
    - Prefer serial number (physical identity)
    - Fallback to device name only if serial missing
    """
    if serial:
        return f"SN:{serial}"
    return f"DN:{device_name}"


def month_to_str(month: str) -> str:
    datetime.strptime(month, "%Y-%m")
    return month


def load_previous_snapshot(path: str) -> Dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f).get("assets", {})


# =====================================================
# Excel Parser (ROBUST)
# =====================================================

def parse_asset_list_xlsx(path: str, month: str) -> Dict[str, dict]:
    """
    Robust Excel asset parser:
    - Auto-detects header row
    - Fuzzy column matching
    - Serial-based asset IDs
    """

    raw = pd.read_excel(path, header=None)

    header_keywords = [
        "device", "computer", "asset",
        "user", "model", "serial",
        "operating", "os"
    ]

    header_row_index = None

    for i in range(len(raw)):
        row_values = [
            str(v).strip().lower()
            for v in raw.iloc[i].values
            if pd.notna(v)
        ]

        matches = sum(
            1 for cell in row_values
            for kw in header_keywords
            if kw in cell
        )

        if matches >= 3:
            header_row_index = i
            break

    if header_row_index is None:
        raise ValueError("❌ Could not detect header row in Asset List Excel file")

    df = pd.read_excel(path, header=header_row_index)
    df.columns = [str(c).strip() for c in df.columns]

    assets = {}

    for _, row in df.iterrows():

        # -------- Device name --------
        device_name = (
            row.get("Device Name")
            or row.get("Computer Name")
            or row.get("Asset Name")
            or ""
        )
        device_name = normalize_device_name(device_name)

        # -------- Serial number --------
        serial = (
            row.get("Serial Number")
            or row.get("Serial")
            or row.get("Serial No")
            or ""
        )
        serial = normalize_serial(serial)

        if not device_name and not serial:
            print("⚠️ Skipped row (no device name or serial):", row.to_dict())
            continue

        asset_id = generate_asset_id(device_name, serial)

        if asset_id in assets:
            print("⚠️ Duplicate asset_id detected (overwriting):", asset_id)

        # -------- Assigned user --------
        user_raw = (
            row.get("Last User")
            or row.get("User")
            or row.get("Assigned User")
            or ""
        )

        user_email = (
            normalize_email(str(user_raw).split("\\")[-1])
            if "@" in str(user_raw)
            else ""
        )

        assets[asset_id] = {
            "device_name": device_name,
            "serial_number": serial or None,
            "assigned_user": user_email or None,
            "type": "workstation",
            "model": str(row.get("Model", "")).strip(),
            "os": (
                str(row.get("Operating System", "")).strip()
                or str(row.get("OS", "")).strip()
            ),
            "status": "active",
            "first_seen": None,   # resolved later
            "last_seen": month,
            "security_state": {
                "edr_installed": False,
                "backup_enabled": False,
                "patched": False
            }
        }

    return assets


# =====================================================
# PDF Parser (Fallback)
# =====================================================

def parse_asset_list_pdf(path: str, month: str) -> Dict[str, dict]:
    assets = {}

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table or len(table) < 2:
                continue

            headers = [str(h).strip() if h else "" for h in table[0]]

            for row in table[1:]:
                data = dict(zip(headers, row))

                device_name = normalize_device_name(
                    data.get("Device Name")
                    or data.get("Computer Name")
                    or ""
                )

                serial = normalize_serial(
                    data.get("Serial Number")
                    or data.get("Serial")
                    or ""
                )

                if not device_name and not serial:
                    continue

                asset_id = generate_asset_id(device_name, serial)

                user_raw = str(data.get("Last User", ""))
                user_email = (
                    normalize_email(user_raw.split("\\")[-1])
                    if "@" in user_raw
                    else ""
                )

                assets[asset_id] = {
                    "device_name": device_name,
                    "serial_number": serial or None,
                    "assigned_user": user_email or None,
                    "type": "workstation",
                    "model": str(data.get("Model", "")).strip(),
                    "os": str(data.get("Operating System", "")).strip(),
                    "status": "active",
                    "first_seen": None,
                    "last_seen": month,
                    "security_state": {
                        "edr_installed": False,
                        "backup_enabled": False,
                        "patched": False
                    }
                }

    return assets


# =====================================================
# First-Seen & Retirement Logic
# =====================================================

def resolve_first_seen(current: Dict, previous: Dict, month: str):
    for asset_id, asset in current.items():
        if asset_id in previous:
            asset["first_seen"] = previous[asset_id].get("first_seen")
        else:
            asset["first_seen"] = month


def mark_retired_assets(current: Dict, previous: Dict):
    retired = {}
    for asset_id, asset in previous.items():
        if asset_id not in current:
            copy = asset.copy()
            copy["status"] = "retired"
            retired[asset_id] = copy
    return retired


def validate_assets(assets: Dict):
    for asset_id, asset in assets.items():
        if not asset.get("first_seen"):
            raise ValueError(f"Missing first_seen for asset: {asset_id}")


# =====================================================
# Main Orchestrator
# =====================================================

def parse_asset_list(
    input_path: str,
    month: str,
    previous_snapshot_path: str,
    output_path: str
):
    month = month_to_str(month)
    previous_assets = load_previous_snapshot(previous_snapshot_path)

    if input_path.lower().endswith(".xlsx"):
        current_assets = parse_asset_list_xlsx(input_path, month)
    elif input_path.lower().endswith(".pdf"):
        current_assets = parse_asset_list_pdf(input_path, month)
    else:
        raise ValueError("Unsupported file format")

    resolve_first_seen(current_assets, previous_assets, month)
    retired_assets = mark_retired_assets(current_assets, previous_assets)
    final_assets = {**current_assets, **retired_assets}

    validate_assets(final_assets)

    snapshot = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "month": month,
            "source": "asset_list"
        },
        "assets": final_assets
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    print("✅ Asset list parsed successfully")
    print(f"   Active devices : {len(current_assets)}")
    print(f"   Retired devices: {len(retired_assets)}")
    print(f"📄 Output written to: {output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Asset List Parser (Serial-Based IDs)")
    parser.add_argument("--input", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--previous", default="")
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    parse_asset_list(
        input_path=args.input,
        month=args.month,
        previous_snapshot_path=args.previous,
        output_path=args.output
    )










# """
# ( device name same so the updated code above which takes serial no as primary and device name as  secondary id)
# Asset List Parser
# -----------------
# Parses Asset List reports (PDF / XLSX) into canonical JSON asset objects.

# Phase: 1 (DB-less).  
# """

# import json
# import os
# from datetime import datetime
# from typing import Dict

# import pandas as pd
# import pdfplumber


# # =========================
# # Utility Functions
# # =========================

# def normalize_device_name(name: str) -> str:
#     if not name:
#         return ""
#     return name.strip().upper()


# def normalize_email(email: str) -> str:
#     if not email:
#         return ""
#     return email.strip().lower()


# def month_to_str(month: str) -> str:
#     try:
#         datetime.strptime(month, "%Y-%m")
#         return month
#     except ValueError:
#         raise ValueError("Month must be in YYYY-MM format")


# def load_previous_snapshot(path: str) -> Dict:
#     if not path or not os.path.exists(path):
#         return {}
#     with open(path, "r") as f:
#         return json.load(f).get("assets", {})


# # =========================
# # Excel Parser
# # =========================
# def parse_asset_list_xlsx(path: str, month: str) -> Dict[str, dict]:
#     """
#     Robust Excel asset parser:
#     - Auto-detects header row
#     - Handles fuzzy column names
#     - Logs skipped & duplicate devices
#     """

#     raw = pd.read_excel(path, header=None)

#     header_keywords = [
#         "device", "computer", "asset",
#         "user", "model", "serial",

#         "operating", "os"
#     ]

#     header_row_index = None

#     for i in range(len(raw)):
#         row_values = [
#             str(v).strip().lower()
#             for v in raw.iloc[i].values
#             if pd.notna(v)
#         ]

#         matches = sum(
#             1 for cell in row_values
#             for kw in header_keywords
#             if kw in cell
#         )

#         if matches >= 3:
#             header_row_index = i
#             break

#     if header_row_index is None:
#         raise ValueError(
#             "❌ Could not detect header row in Asset List Excel file"
#         )

#     df = pd.read_excel(path, header=header_row_index)
#     df.columns = [str(c).strip() for c in df.columns]

#     assets = {}

#     for _, row in df.iterrows():

#         # ---- Device name (flexible) ----
#         device = (
#             row.get("Device Name")
#             or row.get("Computer Name")
#             or row.get("Asset Name")
#             or ""
#         )

#         device = normalize_device_name(device)

#         if not device:
#             print("⚠️ Skipped row (no device name):", row.to_dict())
#             continue

#         # ---- Assigned user (flexible) ----
#         user_raw = (
#             row.get("Last User")
#             or row.get("User")
#             or row.get("Assigned User")
#             or ""
#         )

#         user_email = (
#             normalize_email(str(user_raw).split("\\")[-1])
#             if "@" in str(user_raw)
#             else ""
#         )

#         # ---- Duplicate detection ----
#         if device in assets:
#             print("⚠️ Duplicate device detected (overwriting):", device)

#         assets[device] = {
#             "assigned_user": user_email or None,
#             "type": "workstation",
#             "model": str(row.get("Model", "")).strip(),
#             "serial_number": str(row.get("Serial Number", "")).strip(),
#             "os": (
#                 str(row.get("Operating System", "")).strip()
#                 or str(row.get("OS", "")).strip()
#             ),
#             "status": "active",
#             "first_seen": None,   # resolved later
#             "last_seen": month,
#             "security_state": {
#                 "edr_installed": False,
#                 "backup_enabled": False,
#                 "patched": False
#             }
#         }

#     return assets


# # =========================
# # PDF Parser
# # =========================

# def parse_asset_list_pdf(path: str, month: str) -> Dict[str, dict]:
#     assets = {}

#     with pdfplumber.open(path) as pdf:
#         for page in pdf.pages:
#             table = page.extract_table()
#             if not table or len(table) < 2:
#                 continue

#             headers = [h.strip() if h else "" for h in table[0]]

#             for row in table[1:]:
#                 data = dict(zip(headers, row))

#                 device = normalize_device_name(data.get("Device Name"))
#                 if not device:
#                     continue

#                 user_raw = str(data.get("Last User", ""))
#                 user_email = normalize_email(user_raw.split("\\")[-1]) if "@" in user_raw else ""

#                 assets[device] = {
#                     "assigned_user": user_email or None,
#                     "type": "workstation",
#                     "model": str(data.get("Model", "")).strip(),
#                     "serial_number": str(data.get("Serial Number", "")).strip(),
#                     "os": str(data.get("Operating System", "")).strip(),
#                     "status": "active",
#                     "first_seen": None,
#                     "last_seen": month,
#                     "security_state": {
#                         "edr_installed": False,
#                         "backup_enabled": False,
#                         "patched": False
#                     }
#                 }

#     return assets


# # =========================
# # First-Seen & Retirement Logic
# # =========================

# def resolve_first_seen(current: Dict, previous: Dict, month: str):
#     for device, asset in current.items():
#         if device in previous:
#             asset["first_seen"] = previous[device].get("first_seen")
#         else:
#             asset["first_seen"] = month


# def mark_retired_assets(current: Dict, previous: Dict, month: str):
#     retired = {}

#     for device, asset in previous.items():
#         if device not in current:
#             asset_copy = asset.copy()
#             asset_copy["status"] = "retired"
#             asset_copy["last_seen"] = asset.get("last_seen")
#             retired[device] = asset_copy

#     return retired


# # =========================
# # Validation
# # =========================

# def validate_assets(assets: Dict):
#     seen = set()
#     for device, asset in assets.items():
#         if device in seen:
#             raise ValueError(f"Duplicate device detected: {device}")
#         seen.add(device)

#         if not asset["first_seen"]:
#             raise ValueError(f"Missing first_seen for device: {device}")


# # =========================
# # Main Orchestrator
# # =========================

# def parse_asset_list(
#     input_path: str,
#     month: str,
#     previous_snapshot_path: str,
#     output_path: str
# ):
#     month = month_to_str(month)

#     previous_assets = load_previous_snapshot(previous_snapshot_path)

#     if input_path.lower().endswith(".xlsx"):
#         current_assets = parse_asset_list_xlsx(input_path, month)
#     elif input_path.lower().endswith(".pdf"):
#         current_assets = parse_asset_list_pdf(input_path, month)
#     else:
#         raise ValueError("Unsupported file format (use .pdf or .xlsx)")

#     resolve_first_seen(current_assets, previous_assets, month)

#     retired_assets = mark_retired_assets(current_assets, previous_assets, month)

#     final_assets = {**current_assets, **retired_assets}

#     validate_assets(final_assets)

#     snapshot = {
#         "metadata": {
#             "generated_at": datetime.utcnow().isoformat() + "Z",
#             "month": month,
#             "source": "asset_list"
#         },
#         "assets": final_assets
#     }

#     os.makedirs(os.path.dirname(output_path), exist_ok=True)

#     with open(output_path, "w") as f:
#         json.dump(snapshot, f, indent=2)

#     print(f"✅ Asset list parsed successfully")
#     print(f"   Active devices : {len(current_assets)}")
#     print(f"   Retired devices: {len(retired_assets)}")
#     print(f"📄 Output written to: {output_path}")


# # =========================
# # CLI
# # =========================

# if __name__ == "__main__":
#     """
#     Example:
#     python asset_list_parser.py \
#       --input data/raw/2025-11/asset_list.xlsx \
#       --month 2025-11 \
#       --previous data/normalized/2025-10-assets.json \
#       --output data/normalized/2025-11-assets.json
#     """

#     import argparse

#     parser = argparse.ArgumentParser(description="Asset List Parser")
#     parser.add_argument("--input", required=True, help="Asset list PDF/XLSX path")
#     parser.add_argument("--month", required=True, help="Month in YYYY-MM")
#     parser.add_argument("--previous", required=False, default="", help="Previous asset snapshot")
#     parser.add_argument("--output", required=True, help="Output JSON path")

#     args = parser.parse_args()

#     parse_asset_list(
#         input_path=args.input,
#         month=args.month,
#         previous_snapshot_path=args.previous,
#         output_path=args.output
#     )
