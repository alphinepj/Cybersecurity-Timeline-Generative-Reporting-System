"""
Report Polisher
---------------
Uses an LLM (Mistral via Ollama) to convert a structured,
fact-based narrative into a polished executive security report.

Phase: 3
Design:
- LLM writes prose ONLY
- All facts come from narrative JSON
- Enumeration is mandatory when lists exist
- No hallucination allowed
"""

import json
import os

from prompt_templates import EXECUTIVE_REPORT_PROMPT
from rag_context_loader import load_rag_context
from llm_adapter import run_llm


# =====================================================
# Helpers
# =====================================================

def fmt_list(items):
    """
    Formats lists safely for LLM consumption.
    Explicitly forces enumeration or 'None reported'.
    """
    if not items:
        return "- None reported"
    return "\n".join(f"- {item}" for item in items)


def fmt_paragraphs(items):
    """
    Formats insight bullets into paragraph-ready text.
    """
    if not items:
        return "No notable observations were identified during this period."
    return "\n".join(f"- {item}" for item in items)


# =====================================================
# Main Logic
# =====================================================

def polish_report(narrative_path: str, output_path: str):
    # -------------------------
    # Load narrative
    # -------------------------
    with open(narrative_path, "r", encoding="utf-8") as f:
        narrative = json.load(f)

    rag_context = load_rag_context()

    # -------------------------
    # Extract structured sections
    # -------------------------
    exec_ctx = narrative.get("executive_context", {})
    metrics = exec_ctx.get("metrics", {})

    identity = narrative.get("identity_access", {})
    endpoint = narrative.get("endpoint_security", {})
    threats = narrative.get("threat_analysis", {})
    user_risk = narrative.get("user_risk", {})
    backup = narrative.get("backup_posture", {})

    positives = narrative.get("positive_observations", [])
    recommendations = narrative.get("recommendations", [])

    # -------------------------
    # Build factual LLM context
    # -------------------------
    combined_text = f"""
ABSOLUTE RULES:
- Do NOT invent users, devices, incidents, or metrics.
- If a list is provided, YOU MUST enumerate it.
- If a list is empty, explicitly state that none were identified.
- Do NOT summarize counts without naming entities when names are present.
- Write in professional, executive-level language.

========================
EXECUTIVE METRICS (FACTUAL)
========================
Users joined: {metrics.get('users_joined', 0)}
Users departed: {metrics.get('users_departed', 0)}
Net user change: {metrics.get('net_user_change', 0)}

New devices added: {metrics.get('new_devices', 0)}
Devices retired: {metrics.get('retired_devices', 0)}

Backup coverage: {metrics.get('backup_coverage_percent', 0)}%
Devices without backup: {metrics.get('devices_without_backup', 0)}

Phishing failures: {metrics.get('phishing_failures', 0)}
Critical EDR incidents: {metrics.get('critical_edr_incidents', 0)}

========================
EXECUTIVE BASELINE CONTEXT
========================
{exec_ctx.get("baseline_summary", "")}

========================
IDENTITY & ACCESS MANAGEMENT
========================
Users Joined:
{fmt_list(identity.get("users_joined", []))}

Users Departed:
{fmt_list(identity.get("users_departed", []))}

Identity Observations:
{fmt_paragraphs(identity.get("insights", []))}

========================
ENDPOINT & ASSET SECURITY
========================
Devices Added:
{fmt_list(endpoint.get("devices_added", []))}

Devices Retired:
{fmt_list(endpoint.get("devices_retired", []))}

Endpoint Observations:
{fmt_paragraphs(endpoint.get("insights", []))}

========================
THREAT & INCIDENT ANALYSIS
========================
EDR Incidents:
{fmt_list(threats.get("edr_incidents", []))}

Threat Observations:
{fmt_paragraphs(threats.get("insights", []))}

========================
USER RISK & AWARENESS
========================
Users Failing Phishing:
{fmt_list(user_risk.get("phishing_failures", []))}

Dark Web Exposures:
{fmt_list(user_risk.get("darkweb_exposures", []))}

User Risk Observations:
{fmt_paragraphs(user_risk.get("insights", []))}

========================
BACKUP & RESILIENCE POSTURE
========================
Devices Without Backup:
{fmt_list(backup.get("devices_without_backup", []))}

Backup Observations:
{fmt_paragraphs(backup.get("insights", []))}

========================
POSITIVE SECURITY OBSERVATIONS
========================
{fmt_paragraphs(positives)}

========================
RECOMMENDATIONS & NEXT STEPS
========================
{fmt_paragraphs(recommendations)}
"""

    # -------------------------
    # Build final prompt
    # -------------------------
    prompt = EXECUTIVE_REPORT_PROMPT.format(
        rag_context=rag_context,
        narrative=combined_text
    )

    # -------------------------
    # Run LLM
    # -------------------------
    print("🔹 Generating executive report with Mistral...")
    polished_text = run_llm(prompt)

    # -------------------------
    # Write output
    # -------------------------
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(polished_text)

    print("✅ LLM-polished executive report generated")
    print(f"📄 Report saved to: {os.path.abspath(output_path)}")


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM Report Polisher")
    parser.add_argument(
        "--narrative",
        required=True,
        help="Path to narrative JSON file"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output markdown file path"
    )

    args = parser.parse_args()

    polish_report(
        narrative_path=args.narrative,
        output_path=args.output
    )
