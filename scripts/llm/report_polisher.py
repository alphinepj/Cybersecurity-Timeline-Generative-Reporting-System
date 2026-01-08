import json
import os

from prompt_templates import EXECUTIVE_REPORT_PROMPT
from rag_context_loader import load_rag_context
from llm_adapter import run_llm


def polish_report(narrative_path: str, output_path: str):
    with open(narrative_path, "r") as f:
        narrative = json.load(f)

    rag_context = load_rag_context()

    combined_text = f"""
EXECUTIVE SUMMARY:
{narrative['executive_summary']}

IDENTITY CHANGES:
{chr(10).join(narrative['identity_changes'])}

ASSET CHANGES:
{chr(10).join(narrative['asset_changes'])}

SECURITY FINDINGS:
{chr(10).join(narrative['security_findings'])}

POSITIVE OBSERVATIONS:
{chr(10).join(narrative['positive_observations'])}
"""

    prompt = EXECUTIVE_REPORT_PROMPT.format(
        narrative=combined_text,
        rag_context=rag_context
    )

    polished_text = run_llm(prompt)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(polished_text)

    print("✅ LLM-polished executive report generated")
