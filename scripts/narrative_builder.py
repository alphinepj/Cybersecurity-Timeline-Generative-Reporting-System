"""
Narrative Builder
-----------------
Transforms Insight Engine output into a structured, entity-aware narrative
for executive report generation.

Phase: 2.6
"""

import json
import os
import sys
from datetime import datetime


# =====================================================
# Utilities
# =====================================================

def load_json(path: str):
    if not os.path.exists(path):
        sys.exit(f"❌ Insights file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_list(value):
    """Ensures value is always a list"""
    if isinstance(value, list):
        return value
    return []


# =====================================================
# Metric Extraction (SAFE)
# =====================================================

def compute_metrics(insights: dict) -> dict:
    summary = insights.get("summary_metrics", {})

    return {
        "users_joined": summary.get("users_joined", 0),
        "users_departed": summary.get("users_departed", 0),
        "net_user_change": summary.get("net_user_change", 0),

        "new_devices": summary.get("new_devices", 0),
        "retired_devices": summary.get("retired_devices", 0),

        "backup_coverage_percent": summary.get("backup_coverage_percent", 0),
        "devices_without_backup": summary.get("devices_without_backup", 0),

        "phishing_failures": summary.get("phishing_failures", 0),
        "critical_edr_incidents": summary.get("critical_edr_incidents", 0),
    }


# =====================================================
# Narrative Construction
# =====================================================

def build_narrative(insights: dict) -> dict:
    metrics = compute_metrics(insights)

    return {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "narrative_builder"
        },

        "executive_context": {
            "baseline_summary": insights["summary_metrics"]["executive_summary"],
            "metrics": metrics
        },

        "identity_access": {
            "summary": insights.get("identity_insights", []),
            "users_joined": insights.get("users_joined", []),
            "users_departed": insights.get("users_departed", [])
        },

        "endpoint_security": {
            "summary": insights.get("asset_insights", []),
            "devices_added": insights.get("devices_added", []),
            "devices_retired": insights.get("devices_retired", [])
        },

        "threat_analysis": {
            "summary": insights.get("security_risks", []),
            "phishing_failed_users": insights.get("phishing_failed_users", []),
            "darkweb_exposed_users": insights.get("darkweb_exposed_users", [])
        },

        "backup_posture": {
            "devices_without_backup": insights.get("devices_without_backup_list", [])
        },

        "positive_observations": insights.get("positive_findings", []),
        "recommendations": insights.get("recommendations", [])
    }


# =====================================================
# Main Orchestrator
# =====================================================

def run_narrative_builder(insights_path: str, output_path: str):
    insights = load_json(insights_path)
    narrative = build_narrative(insights)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    abs_output_path = os.path.abspath(output_path)

    with open(abs_output_path, "w", encoding="utf-8") as f:
        json.dump(narrative, f, indent=2)

    print("✅ Narrative Builder completed")
    print(f"📄 Narrative written to: {abs_output_path}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Narrative Builder")
    parser.add_argument("--insights", required=True, help="Insights JSON file")
    parser.add_argument("--output", required=True, help="Narrative JSON output")

    args = parser.parse_args()

    run_narrative_builder(
        insights_path=args.insights,
        output_path=args.output
    )
