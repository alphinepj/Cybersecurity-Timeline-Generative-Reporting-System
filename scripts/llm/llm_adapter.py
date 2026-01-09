"""
LLM Adapter — Mistral via Ollama
-------------------------------
Stable, CPU-safe Mistral execution.
"""

import subprocess
import json


def run_llm(prompt: str) -> str:
    process = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return process.stdout.decode("utf-8").strip()
