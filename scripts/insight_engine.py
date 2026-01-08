"""
Insight Engine
--------------
Converts enriched data + diffs into deterministic security insights.

Phase: 2
Design:
- No AI
- Fully explainable
- Executive & auditor friendly
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
    with open(path, "r") as f:
        return json.load(f)


def empty_diff() -> Dict:
    """
    Used when no previous month exists
    """
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

def analyze_identity(diff: Dict) -> List[str]:
    insights = []

    new_users = len(diff["users"]["new_users"])
    resigned_users = len(diff["users"]["resigned_users"])

    if new_users > 0:
        insights.append(f"{new_users} new user(s) were onboarded during the period.")

    if resigned_users > 0:
        insights.append(f"{resigned_users} user(s) were deprovisioned during the period.")

    return insights


# =====================================================
# Asset Insights
# =====================================================

def analyze_assets(diff: Dict) -> List[str]:
    insights = []

    new_devices = len(diff["assets"]["new_devices"])
    retired_devices = len(diff["assets"]["retired_devices"])

    if new_devices > 0:
        insights.append(f"{new_devices} new workstation(s) were added.")

    if retired_devices > 0:
        insights.append(f"{retired_devices} workstation(s) were retired.")

    return insights


# =====================================================
# Security Risk Detection
# =====================================================

def analyze_security_risks(users: Dict, assets: Dict) -> List[str]:
    risks = []

    for email, user in users["users"].items():
        risk = user.get("risk_signals", {})

        if risk.get("phishing_risk") == "high":
            risks.append(f"User {email} failed a phishing simulation.")

        if risk.get("dark_web_exposed"):
            risks.append(
                f"User {email} credentials were found on the dark web "
                f"(severity: {risk.get('dark_web_severity')})."
            )

    for asset in assets["assets"].values():
        backup = asset.get("backup_state", {})
        sec = asset.get("security_state", {})

        if backup.get("risk_level") == "critical":
            risks.append(
                f"Asset {asset.get('device_name')} has failing backups."
            )

        if backup.get("enabled") is False:
            risks.append(
                f"Asset {asset.get('device_name')} does not have backups configured."
            )

        if sec.get("risk_level") == "high":
            risks.append(
                f"Asset {asset.get('device_name')} has unresolved EDR incidents."
            )

    return risks


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
# Summary Metrics
# =====================================================

def build_summary(users: Dict, assets: Dict, diff: Dict) -> Dict:
    return {
        "total_users": len(users["users"]),
        "total_assets": len(assets["assets"]),
        "user_change": diff["metrics"]["user_count_change"],
        "asset_change": diff["metrics"]["device_count_change"]
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

    insights = {
        "summary_metrics": build_summary(users, assets, diff),
        "identity_insights": analyze_identity(diff),
        "asset_insights": analyze_assets(diff),
        "security_risks": analyze_security_risks(users, assets),
        "positive_findings": analyze_positives(users, assets),
        "trend_indicators": []
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
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











# """
# Insight Engine
# --------------
# Converts enriched data + diffs into deterministic security insights.

# Phase: 2
# Design:
# - No AI
# - Fully explainable
# - Executive & auditor friendly
# """

# import json
# import os
# from typing import Dict, List


# # =====================================================
# # Loaders
# # =====================================================

# def load_json(path: str) -> Dict:
#     if not os.path.exists(path):
#         raise FileNotFoundError(f"File not found: {path}")
#     with open(path, "r") as f:
#         return json.load(f)


# # =====================================================
# # Identity Insights
# # =====================================================

# def analyze_identity(diff: Dict) -> List[str]:
#     insights = []

#     new_users = len(diff["users"].get("new_users", []))
#     resigned_users = len(diff["users"].get("resigned_users", []))

#     if new_users > 0:
#         insights.append(f"{new_users} new user(s) were onboarded during the period.")

#     if resigned_users > 0:
#         insights.append(f"{resigned_users} user(s) were deprovisioned during the period.")

#     return insights


# # =====================================================
# # Asset Insights
# # =====================================================

# def analyze_assets(diff: Dict) -> List[str]:
#     insights = []

#     new_devices = len(diff["assets"].get("new_devices", []))
#     retired_devices = len(diff["assets"].get("retired_devices", []))

#     if new_devices > 0:
#         insights.append(f"{new_devices} new workstation(s) were added.")

#     if retired_devices > 0:
#         insights.append(f"{retired_devices} workstation(s) were retired.")

#     return insights


# # =====================================================
# # Security Risk Detection
# # =====================================================

# def analyze_security_risks(users: Dict, assets: Dict) -> List[str]:
#     risks = []

#     # ---- User risks ----
#     for email, user in users["users"].items():
#         risk = user.get("risk_signals", {})

#         if risk.get("phishing_risk") == "high":
#             risks.append(f"User {email} failed a phishing simulation.")

#         if risk.get("dark_web_exposed"):
#             risks.append(
#                 f"User {email} credentials were found on the dark web "
#                 f"(severity: {risk.get('dark_web_severity')})."
#             )

#     # ---- Asset risks ----
#     for asset_id, asset in assets["assets"].items():
#         sec = asset.get("security_state", {})
#         backup = asset.get("backup_state", {})

#         if sec.get("risk_level") == "high":
#             risks.append(
#                 f"Asset {asset.get('device_name')} has unresolved EDR incidents."
#             )

#         if backup.get("risk_level") == "critical":
#             risks.append(
#                 f"Asset {asset.get('device_name')} has failing backups."
#             )

#         if backup.get("enabled") is False:
#             risks.append(
#                 f"Asset {asset.get('device_name')} does not have backups configured."
#             )

#     return risks


# # =====================================================
# # Positive Findings
# # =====================================================

# def analyze_positives(users: Dict, assets: Dict) -> List[str]:
#     positives = []

#     phishing_failures = [
#         u for u in users["users"].values()
#         if u.get("risk_signals", {}).get("phishing_clicked")
#     ]

#     if len(phishing_failures) == 0:
#         positives.append("No users failed phishing simulations this period.")

#     critical_backups = [
#         a for a in assets["assets"].values()
#         if a.get("backup_state", {}).get("risk_level") == "critical"
#     ]

#     if len(critical_backups) == 0:
#         positives.append("All monitored devices have healthy backup status.")

#     high_edr = [
#         a for a in assets["assets"].values()
#         if a.get("security_state", {}).get("risk_level") == "high"
#     ]

#     if len(high_edr) == 0:
#         positives.append("No high-severity EDR incidents were detected.")

#     return positives


# # =====================================================
# # Summary Metrics
# # =====================================================

# def build_summary(users: Dict, assets: Dict, diff: Dict) -> Dict:
#     return {
#         "total_users": len(users["users"]),
#         "total_assets": len(assets["assets"]),
#         "user_change": diff["metrics"].get("user_count_change"),
#         "asset_change": diff["metrics"].get("device_count_change")
#     }


# # =====================================================
# # Main Engine
# # =====================================================

# def run_insight_engine(
#     users_path: str,
#     assets_path: str,
#     diff_path: str,
#     output_path: str
# ):
#     users = load_json(users_path)
#     assets = load_json(assets_path)
#     diff = load_json(diff_path)

#     insights = {
#         "summary_metrics": build_summary(users, assets, diff),
#         "identity_insights": analyze_identity(diff),
#         "asset_insights": analyze_assets(diff),
#         "security_risks": analyze_security_risks(users, assets),
#         "positive_findings": analyze_positives(users, assets),
#         "trend_indicators": []
#     }

#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     with open(output_path, "w") as f:
#         json.dump(insights, f, indent=2)

#     print("✅ Insight Engine completed")
#     print(f"📄 Insights written to: {output_path}")


# # =====================================================
# # CLI
# # =====================================================

# if __name__ == "__main__":
#     import argparse

#     parser = argparse.ArgumentParser(description="Insight Engine")
#     parser.add_argument("--users", required=True)
#     parser.add_argument("--assets", required=True)
#     parser.add_argument("--diff", required=True)
#     parser.add_argument("--output", required=True)

#     args = parser.parse_args()

#     run_insight_engine(
#         users_path=args.users,
#         assets_path=args.assets,
#         diff_path=args.diff,
#         output_path=args.output
#     )
