"""
Diff Engine
-----------
Compares month-to-month user & asset snapshots and produces a change log.

Phase: 1 (DB-less)
"""

import json
import os
from datetime import datetime
from typing import Dict


# =========================
# Loaders
# =========================

def load_snapshot(path: str, key: str) -> Dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f).get(key, {})


# =========================
# User Diff
# =========================

def diff_users(prev: Dict, curr: Dict) -> Dict:
    prev_set = set(prev.keys())
    curr_set = set(curr.keys())

    new_users = sorted(curr_set - prev_set)
    resigned_users = sorted(prev_set - curr_set)

    service_changes = {}

    for email in prev_set & curr_set:
        prev_services = prev[email].get("services", {})
        curr_services = curr[email].get("services", {})

        added = [s for s in curr_services if curr_services.get(s) and not prev_services.get(s)]
        removed = [s for s in prev_services if prev_services.get(s) and not curr_services.get(s)]

        if added or removed:
            service_changes[email] = {
                "added": added,
                "removed": removed
            }

    return {
        "new_users": new_users,
        "resigned_users": resigned_users,
        "service_changes": service_changes
    }


# =========================
# Asset Diff
# =========================

def diff_assets(prev: Dict, curr: Dict) -> Dict:
    prev_set = set(prev.keys())
    curr_set = set(curr.keys())

    new_devices = sorted(curr_set - prev_set)
    retired_devices = sorted(prev_set - curr_set)

    ownership_changes = {}

    for device in prev_set & curr_set:
        prev_user = prev[device].get("assigned_user")
        curr_user = curr[device].get("assigned_user")

        if prev_user != curr_user:
            ownership_changes[device] = {
                "from": prev_user,
                "to": curr_user
            }

    return {
        "new_devices": new_devices,
        "retired_devices": retired_devices,
        "ownership_changes": ownership_changes
    }


# =========================
# Security Alerts
# =========================

def generate_alerts(user_diff: Dict, asset_diff: Dict, assets: Dict) -> list:
    alerts = []

    for device, asset in assets.items():
        if asset.get("status") == "active" and not asset.get("assigned_user"):
            alerts.append({
                "type": "orphaned_device",
                "severity": "high",
                "message": f"Device {device} has no assigned user"
            })

    for email in user_diff["resigned_users"]:
        for device, asset in assets.items():
            if asset.get("assigned_user") == email:
                alerts.append({
                    "type": "resigned_user_device",
                    "severity": "critical",
                    "message": f"Resigned user {email} still has device {device}"
                })

    return alerts


# =========================
# Metrics
# =========================

def generate_metrics(prev_users, curr_users, prev_assets, curr_assets):
    return {
        "user_count_change": len(curr_users) - len(prev_users),
        "device_count_change": len(curr_assets) - len(prev_assets)
    }


# =========================
# Main
# =========================

def generate_diff(
    prev_users_path: str,
    curr_users_path: str,
    prev_assets_path: str,
    curr_assets_path: str,
    output_path: str,
    from_month: str,
    to_month: str
):
    prev_users = load_snapshot(prev_users_path, "users")
    curr_users = load_snapshot(curr_users_path, "users")

    prev_assets = load_snapshot(prev_assets_path, "assets")
    curr_assets = load_snapshot(curr_assets_path, "assets")

    user_diff = diff_users(prev_users, curr_users)
    asset_diff = diff_assets(prev_assets, curr_assets)

    alerts = generate_alerts(user_diff, asset_diff, curr_assets)
    metrics = generate_metrics(prev_users, curr_users, prev_assets, curr_assets)

    diff_report = {
        "metadata": {
            "from_month": from_month,
            "to_month": to_month,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        },
        "users": user_diff,
        "assets": asset_diff,
        "metrics": metrics,
        "alerts": alerts
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(diff_report, f, indent=2)

    print("✅ Diff generated successfully")
    print(f"📄 Output: {output_path}")
    print(f"👤 User change: {metrics['user_count_change']}")
    print(f"💻 Device change: {metrics['device_count_change']}")


# =========================
# CLI
# =========================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monthly Diff Engine")
    parser.add_argument("--prev-users", required=True)
    parser.add_argument("--curr-users", required=True)
    parser.add_argument("--prev-assets", required=True)
    parser.add_argument("--curr-assets", required=True)
    parser.add_argument("--from-month", required=True)
    parser.add_argument("--to-month", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    generate_diff(
        prev_users_path=args.prev_users,
        curr_users_path=args.curr_users,
        prev_assets_path=args.prev_assets,
        curr_assets_path=args.curr_assets,
        output_path=args.output,
        from_month=args.from_month,
        to_month=args.to_month
    )
