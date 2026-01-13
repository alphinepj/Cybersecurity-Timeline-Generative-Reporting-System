# scripts/dash_app/data_loader.py

import json
from pathlib import Path

DASHBOARD_DIR = Path("data/dashboard")

def load_dashboard_data(month: str):
    path = DASHBOARD_DIR / f"{month}.json"
    if not path.exists():
        raise FileNotFoundError(f"Dashboard data not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
