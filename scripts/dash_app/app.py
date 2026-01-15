# scripts/dash_app/app.py

import json
from pathlib import Path

import dash
import dash_bootstrap_components as dbc

from layout import build_layout




# =====================================================
# Load dashboard snapshot (AUTHORITATIVE)
# =====================================================

DASHBOARD_JSON = Path("data/dashboard/2025-11-dashboard.json")

if not DASHBOARD_JSON.exists():
    raise FileNotFoundError(f"Dashboard data not found: {DASHBOARD_JSON}")

with open(DASHBOARD_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# 🔴 HARD ASSERTS (to catch silent bugs)
assert "client" in data
assert "kpis" in data
assert "risk_posture" in data
assert "identity" in data
assert "assets" in data
assert "security" in data

print("✅ Dashboard data loaded successfully")
print("🔎 Keys:", data.keys())



print("🔥 DASHBOARD DATA FILE LOADED")
print("Keys:", data.keys())
print("Client:", data.get("client"))
print("Month:", data.get("month"))

# =====================================================
# Dash App
# =====================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.layout = build_layout(data)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, port=8051)
