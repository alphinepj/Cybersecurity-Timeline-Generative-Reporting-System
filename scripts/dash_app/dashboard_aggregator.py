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
# KPI Extraction (Aligned with Insight Engine)
# =====================================================

def extract_kpis(insights: Dict) -> Dict:
    summary = insights.get("summary_metrics", {})

    return {
        # Headline counts
        "total_users": summary.get("total_users", 0),
        "total_devices": summary.get("total_assets", 0),

        # Net changes (already computed upstream)
        "net_user_change": summary.get("user_change", 0),
        "net_device_change": summary.get("asset_change", 0),

        # Event counts (derived from insight lists, not raw data)
        "identity_events": len(insights.get("identity_insights", [])),
        "asset_events": len(insights.get("asset_insights", [])),
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
# Detail Sections (Text-Preserving)
# =====================================================

def extract_identity(insights: Dict) -> Dict:
    return {
        "events": insights.get("identity_insights", [])
    }


def extract_assets(insights: Dict) -> Dict:
    return {
        "events": insights.get("asset_insights", [])
    }


def extract_security(insights: Dict) -> Dict:
    return {
        "risks": insights.get("security_risks", []),
        "positives": insights.get("positive_findings", [])
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
        # Top-level identity (UI-safe)
        "client": client,
        "month": month,

        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "dashboard_aggregator"
        },

        # KPIs & posture
        "kpis": extract_kpis(insights),
        "risk_posture": determine_risk_posture(insights),

        # Detail sections (verbatim)
        "identity": extract_identity(insights),
        "assets": extract_assets(insights),
        "security": extract_security(insights),

        # Report artifacts
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
