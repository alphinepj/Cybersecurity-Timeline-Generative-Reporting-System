import dash_bootstrap_components as dbc
from dash import html
from components.kpi_cards import kpi_card


def build_layout(data):
    kpis = data["kpis"]
    risk = data["risk_posture"]
    security = data.get("security", {})
    positives = security.get("positives", [])

    return dbc.Container(
        fluid=True,
        children=[

            # ======================
            # Header
            # ======================
            html.H2(f"{data['client']} — Security Dashboard"),
            html.H5(f"Reporting Month: {data['month']}"),
            html.Hr(),

            # ======================
            # KPI Cards
            # ======================
            dbc.Row([
                dbc.Col(kpi_card("Total Users", kpis["total_users"]), md=2),
                dbc.Col(kpi_card("Total Devices", kpis["total_devices"]), md=2),
                dbc.Col(kpi_card("Net User Change", kpis["net_user_change"], "info"), md=2),
                dbc.Col(kpi_card("Net Device Change", kpis["net_device_change"], "info"), md=2),
                dbc.Col(kpi_card("Identity Events", kpis["identity_events"], "warning"), md=2),
                dbc.Col(kpi_card("Security Risks", kpis["security_risks"], "danger"), md=2),
            ], className="mb-4"),

            html.Hr(),

            # ======================
            # Risk Posture Summary
            # ======================
            dbc.Alert(
                f"Overall Risk Posture: {risk['overall'].upper()} — {risk['summary']}",
                color="success" if risk["overall"] == "low" else "warning",
            ),

            html.Hr(),

            # ======================
            # Identity Events
            # ======================
            html.H4("Identity & Access Events"),
            html.Ul(
                [html.Li(e) for e in data["identity"].get("events", [])]
                or [html.Li("No identity events recorded.")]
            ),

            html.Hr(),

            # ======================
            # Asset Events
            # ======================
            html.H4("Endpoint & Asset Events"),
            html.Ul(
                [html.Li(e) for e in data["assets"].get("events", [])]
                or [html.Li("No asset events recorded.")]
            ),

            html.Hr(),

            # ======================
            # Positive Observations
            # ======================
            html.H4("Positive Security Observations"),
            html.Ul(
                [html.Li(p) for p in positives]
                if positives
                else [html.Li("No positive observations recorded.")]
            ),
        ],
    )
