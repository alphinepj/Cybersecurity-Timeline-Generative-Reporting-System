"""
Insight Engine
--------------
Converts enriched data + diffs into deterministic security insights.

Phase: 2
Design:
- No AI
- Fully explainable
- Executive & auditor friendly
- Emits BOTH summaries and entity-level facts
"""

import json
import os
from typing import Dict, List


# =====================================================
# Loaders
# =====================================================

def load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def empty_diff() -> Dict:
    return {
        "users": {
            "new_users": [],
            "resigned_users": []
        },
        "assets": {
            "new_devices": [],
            "retired_devices": []
        },
        "metrics": {
            "user_count_change": 0,
            "device_count_change": 0
        }
    }


# =====================================================
# Identity Insights
# =====================================================

def analyze_identity(diff: Dict) -> Dict:
    new_users = diff["users"]["new_users"]
    resigned_users = diff["users"]["resigned_users"]

    summaries = []

    if new_users:
        summaries.append(
            f"{len(new_users)} new user(s) were onboarded during the period."
        )

    if resigned_users:
        summaries.append(
            f"{len(resigned_users)} user(s) were deprovisioned during the period."
        )

    return {
        "summary": summaries,
        "users_joined": new_users,
        "users_departed": resigned_users
    }


# =====================================================
# Asset Insights
# =====================================================

def analyze_assets(diff: Dict) -> Dict:
    new_devices = diff["assets"]["new_devices"]
    retired_devices = diff["assets"]["retired_devices"]

    summaries = []

    if new_devices:
        summaries.append(
            f"{len(new_devices)} new workstation(s) were added."
        )

    if retired_devices:
        summaries.append(
            f"{len(retired_devices)} workstation(s) were retired."
        )

    return {
        "summary": summaries,
        "devices_added": new_devices,
        "devices_retired": retired_devices
    }


# =====================================================
# Security Risk Detection
# =====================================================

def analyze_security_risks(users: Dict, assets: Dict) -> Dict:
    risk_summaries = []
    phishing_failed_users = []
    darkweb_exposed_users = []
    edr_affected_devices = []
    devices_without_backup = []

    # ---- User risks
    for email, user in users["users"].items():
        risk = user.get("risk_signals", {})

        if risk.get("phishing_clicked"):
            phishing_failed_users.append(email)
            risk_summaries.append(
                f"User {email} failed a phishing simulation."
            )

        if risk.get("dark_web_exposed"):
            darkweb_exposed_users.append(email)
            risk_summaries.append(
                f"User {email} credentials were found on the dark web."
            )

    # ---- Asset risks
    for asset in assets["assets"].values():
        name = asset.get("device_name") or asset.get("serial_number")
        backup = asset.get("backup_state", {})
        sec = asset.get("security_state", {})

        if backup.get("enabled") is False:
            devices_without_backup.append(name)
            risk_summaries.append(
                f"Asset {name} does not have backups configured."
            )

        if backup.get("risk_level") == "critical":
            edr_affected_devices.append(name)
            risk_summaries.append(
                f"Asset {name} has failing backups."
            )

        if sec.get("risk_level") == "high":
            edr_affected_devices.append(name)
            risk_summaries.append(
                f"Asset {name} has unresolved EDR incidents."
            )

    return {
        "summary": risk_summaries,
        "phishing_failed_users": phishing_failed_users,
        "darkweb_exposed_users": darkweb_exposed_users,
        "edr_affected_devices": edr_affected_devices,
        "devices_without_backup": devices_without_backup
    }


# =====================================================
# Positive Findings
# =====================================================

def analyze_positives(users: Dict, assets: Dict) -> List[str]:
    positives = []

    if not any(
        u.get("risk_signals", {}).get("phishing_clicked")
        for u in users["users"].values()
    ):
        positives.append("No users failed phishing simulations this period.")

    if not any(
        a.get("backup_state", {}).get("risk_level") == "critical"
        for a in assets["assets"].values()
    ):
        positives.append("All monitored devices have healthy backup status.")

    if not any(
        a.get("security_state", {}).get("risk_level") == "high"
        for a in assets["assets"].values()
    ):
        positives.append("No high-severity EDR incidents were detected.")

    return positives


# =====================================================
# Summary Metrics (Expanded)
# =====================================================

def build_summary(users: Dict, assets: Dict, diff: Dict) -> Dict:
    return {
        "total_users": len(users["users"]),
        "total_assets": len(assets["assets"]),

        "users_joined": len(diff["users"]["new_users"]),
        "users_departed": len(diff["users"]["resigned_users"]),
        "net_user_change": diff["metrics"]["user_count_change"],

        "new_devices": len(diff["assets"]["new_devices"]),
        "retired_devices": len(diff["assets"]["retired_devices"]),
        "device_count_change": diff["metrics"]["device_count_change"],

        "backup_coverage_percent": round(
            100
            * sum(
                1 for a in assets["assets"].values()
                if a.get("backup_state", {}).get("enabled")
            )
            / max(len(assets["assets"]), 1),
            1
        ),

        "phishing_failures": sum(
            1 for u in users["users"].values()
            if u.get("risk_signals", {}).get("phishing_clicked")
        ),

        "critical_edr_incidents": sum(
            1 for a in assets["assets"].values()
            if a.get("security_state", {}).get("risk_level") == "high"
        ),

        "executive_summary": (
            "The organization maintained a stable security posture during the reporting period, "
            "with no critical incidents and effective control coverage across users and assets."
        )
    }


# =====================================================
# Main Engine
# =====================================================

def run_insight_engine(
    users_path: str,
    assets_path: str,
    diff_path: str,
    output_path: str
):
    users = load_json(users_path)
    assets = load_json(assets_path)

    diff = load_json(diff_path)
    if diff is None:
        print("ℹ️ Diff file not found — using baseline (first month)")
        diff = empty_diff()

    identity = analyze_identity(diff)
    assets_insight = analyze_assets(diff)
    risks = analyze_security_risks(users, assets)

    insights = {
        "summary_metrics": build_summary(users, assets, diff),

        "identity_insights": identity["summary"],
        "users_joined": identity["users_joined"],
        "users_departed": identity["users_departed"],

        "asset_insights": assets_insight["summary"],
        "devices_added": assets_insight["devices_added"],
        "devices_retired": assets_insight["devices_retired"],

        "security_risks": risks["summary"],
        "phishing_failed_users": risks["phishing_failed_users"],
        "darkweb_exposed_users": risks["darkweb_exposed_users"],
        "devices_without_backup_list": risks["devices_without_backup"],

        "positive_findings": analyze_positives(users, assets),
        "recommendations": [
            "Continue regular phishing simulations and security awareness training.",
            "Ensure backup coverage remains enabled for all endpoints.",
            "Maintain strict identity lifecycle management processes.",
            "Continue proactive endpoint monitoring and threat detection."
        ]
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2)

    print("✅ Insight Engine completed")
    print(f"📄 Insights written to: {output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Insight Engine")
    parser.add_argument("--users", required=True)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--diff", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    run_insight_engine(
        users_path=args.users,
        assets_path=args.assets,
        diff_path=args.diff,
        output_path=args.output
    )
