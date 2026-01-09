"""
Report Polisher
---------------
Uses an LLM (Mistral) to convert a structured narrative
into a polished executive report.
"""

import json
import os

from prompt_templates import EXECUTIVE_REPORT_PROMPT
from rag_context_loader import load_rag_context
from llm_adapter import run_llm


def polish_report(narrative_path: str, output_path: str):
    with open(narrative_path, "r", encoding="utf-8") as f:
        narrative = json.load(f)

    rag_context = load_rag_context()

    combined_text = f"""
EXECUTIVE SUMMARY:
{narrative.get('executive_summary', '')}

IDENTITY CHANGES:
{chr(10).join(narrative.get('identity_changes', []))}

ASSET CHANGES:
{chr(10).join(narrative.get('asset_changes', []))}

SECURITY FINDINGS:
{chr(10).join(narrative.get('security_findings', []))}

POSITIVE OBSERVATIONS:
{chr(10).join(narrative.get('positive_observations', []))}

RECOMMENDATIONS:
{chr(10).join(narrative.get('recommendations', []))}
"""

    prompt = EXECUTIVE_REPORT_PROMPT.format(
        rag_context=rag_context,
        narrative=combined_text
    )

    print("🔹 Generating executive report with Mistral...")
    polished_text = run_llm(prompt)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(polished_text)

    print("✅ LLM-polished executive report generated")
    print(f"📄 Report saved to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM Report Polisher")
    parser.add_argument("--narrative", required=True, help="Narrative JSON file")
    parser.add_argument("--output", required=True, help="Output markdown file")

    args = parser.parse_args()

    polish_report(
        narrative_path=args.narrative,
        output_path=args.output
    )
