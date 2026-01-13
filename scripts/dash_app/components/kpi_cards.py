# scripts/dash_app/components/kpi_cards.py

import dash_bootstrap_components as dbc
from dash import html

def kpi_card(title, value, color="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title"),
            html.H2(value, className="card-text")
        ]),
        color=color,
        inverse=True
    )
