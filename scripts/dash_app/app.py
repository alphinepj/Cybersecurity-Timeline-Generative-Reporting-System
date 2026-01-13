# scripts/dash_app/app.py

import dash
import dash_bootstrap_components as dbc
from data_loader import load_dashboard_data
from layout import build_layout

MONTH = "2025-11"  # later → dropdown selector

data = load_dashboard_data(MONTH)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

app.layout = build_layout(data)

if __name__ == "__main__":
    app.run(
    debug=True,
    port=8050,
    use_reloader=False
    )

