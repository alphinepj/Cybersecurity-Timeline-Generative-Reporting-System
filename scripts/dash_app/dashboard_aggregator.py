"""
Dashboard Aggregator
--------------------
Builds a deterministic dashboard snapshot from insight engine output.

Phase: Dashboard Layer (Read-only)
Design principles:
- No AI
- No recomputation of business logic
- Fully explainable
"""

import json
import os
from datetime import datetime
from typing import Dict


# =====================================================
# Utilities
# =====================================================

def load_json(path: str) -> Dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================================================
# KPI Extraction (CANONICAL & DASH-SAFE)
# =====================================================

def extract_kpis(insights: Dict) -> Dict:
    summary = insights.get("summary_metrics", {})

    return {
        # Totals
        "total_users": summary.get("total_users", 0),
        "total_devices": summary.get("total_assets", 0),

        # Activity (explicit)
        "users_joined": len(insights.get("users_joined", [])),
        "users_departed": len(insights.get("users_departed", [])),
        "devices_added": len(insights.get("devices_added", [])),
        "devices_retired": len(insights.get("devices_retired", [])),

        # Net deltas (from diff engine)
        "net_user_change": summary.get("net_user_change", 0),
        "net_device_change": summary.get("device_count_change", 0),

        # Risk posture
        "security_risks": len(insights.get("security_risks", [])),
        "positive_findings": len(insights.get("positive_findings", [])),
    }


# =====================================================
# Risk Posture (Deterministic)
# =====================================================

def determine_risk_posture(insights: Dict) -> Dict:
    risks = insights.get("security_risks", [])

    return {
        "overall": "low" if not risks else "elevated",
        "risk_count": len(risks),
        "summary": (
            "No material security risks identified during the period."
            if not risks else
            "One or more security risks require attention."
        )
    }


# =====================================================
# Detail Sections (Lists preserved verbatim)
# =====================================================

def extract_identity(insights: Dict) -> Dict:
    return {
        "events": insights.get("identity_insights", []),
        "users_joined": insights.get("users_joined", []),
        "users_departed": insights.get("users_departed", []),
    }


def extract_assets(insights: Dict) -> Dict:
    return {
        "events": insights.get("asset_insights", []),
        "devices_added": insights.get("devices_added", []),
        "devices_retired": insights.get("devices_retired", []),
    }


def extract_security(insights: Dict) -> Dict:
    return {
        "risks": insights.get("security_risks", []),
        "positives": insights.get("positive_findings", []),
    }


# =====================================================
# Main Aggregator
# =====================================================

def build_dashboard(
    client: str,
    month: str,
    insights_path: str,
    output_path: str
):
    insights = load_json(insights_path)

    dashboard = {
        # Dash-safe identity
        "client": client,
        "month": month,

        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "dashboard_aggregator"
        },

        # KPIs
        "kpis": extract_kpis(insights),

        # Risk posture
        "risk_posture": determine_risk_posture(insights),

        # Detailed sections (for tables)
        "identity": extract_identity(insights),
        "assets": extract_assets(insights),
        "security": extract_security(insights),

        # Artifacts
        "artifacts": {
            "executive_report_pdf": f"reports/{month}/executive_report.pdf",
            "executive_report_md": f"reports/{month}/executive_report_polished.md"
        }
    }

    save_json(dashboard, output_path)

    print("✅ Dashboard snapshot generated")
    print(f"📊 Dashboard data written to: {os.path.abspath(output_path)}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dashboard Aggregator")
    parser.add_argument("--client", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--insights", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    build_dashboard(
        client=args.client,
        month=args.month,
        insights_path=args.insights,
        output_path=args.output
    )
