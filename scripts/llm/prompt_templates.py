EXECUTIVE_REPORT_PROMPT = """
You are an assistant generating an EXECUTIVE CYBERSECURITY REPORT.

STRICT RULES (DO NOT VIOLATE):
- Do NOT invent facts
- Do NOT add risks or findings
- Do NOT change numbers
- Do NOT speculate
- Only rewrite and improve language
- Maintain executive, non-technical tone

FACTUAL CONTENT (DO NOT MODIFY MEANING):
{narrative}

CONTEXT (FOR STYLE ONLY):
{rag_context}

TASK:
Rewrite the content clearly and professionally for an executive audience.
Return ONLY the rewritten text.
"""
