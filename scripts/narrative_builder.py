import json
import os
import sys


def load_json(path: str):
    if not os.path.exists(path):
        sys.exit(f"❌ Insights file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_narrative(insights):
    return {
        "executive_summary": insights.get("summary_metrics", {}).get(
            "executive_summary",
            "Security posture remains stable for the reporting period."
        ),
        "identity_changes": insights.get("identity_insights", []),
        "asset_changes": insights.get("asset_insights", []),
        "security_findings": insights.get("security_risks", []),
        "positive_observations": insights.get("positive_findings", [])
    }


def run_narrative_builder(insights_path: str, output_path: str):
    insights = load_json(insights_path)

    narrative = build_narrative(insights)

    # 🔑 THIS IS THE CRITICAL FIX
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    abs_output_path = os.path.abspath(output_path)

    with open(abs_output_path, "w", encoding="utf-8") as f:
        json.dump(narrative, f, indent=2)

    print("✅ Narrative Builder completed")
    print(f"📄 Narrative written to: {abs_output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Narrative Builder")
    parser.add_argument("--insights", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    run_narrative_builder(
        insights_path=args.insights,
        output_path=args.output
    )
