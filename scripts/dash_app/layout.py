import dash_bootstrap_components as dbc
from dash import html
from components.kpi_cards import kpi_card


# -------------------------------------------------
# Small helper to render simple tables
# -------------------------------------------------
def simple_table(title, items, empty_msg):
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, className="card-title"),
            html.Table(
                [
                    html.Thead(html.Tr([html.Th("Value")])),
                    html.Tbody(
                        [html.Tr([html.Td(i)]) for i in items]
                        if items else
                        [html.Tr([html.Td(empty_msg)])]
                    ),
                ],
                className="table table-sm table-striped",
            ),
        ]),
        className="mb-4",
    )


def build_layout(data):
    # ----------------------
    # Safe Extraction
    # ----------------------
    kpis = data.get("kpis", {})
    risk = data.get("risk_posture", {})

    identity = data.get("identity", {})
    assets = data.get("assets", {})
    security = data.get("security", {})

    identity_events = identity.get("events", [])
    users_joined = identity.get("users_joined", [])
    users_departed = identity.get("users_departed", [])

    asset_events = assets.get("events", [])
    devices_added = assets.get("devices_added", [])
    devices_retired = assets.get("devices_retired", [])

    positives = security.get("positives", [])

    return dbc.Container(
        fluid=True,
        children=[

            # ======================
            # Header
            # ======================
            html.H2(f"{data.get('client', 'Unknown Client')} — Security Dashboard"),
            html.H5(f"Reporting Month: {data.get('month', 'Unknown')}"),
            html.Hr(),

            # ======================
            # KPI ROW — USERS
            # ======================
            dbc.Row([
                dbc.Col(kpi_card("Total Users", kpis.get("total_users", 0)), md=2),
                dbc.Col(kpi_card("Users Joined", kpis.get("users_joined", 0), "success"), md=2),
                dbc.Col(kpi_card("Users Departed", kpis.get("users_departed", 0), "warning"), md=2),
                dbc.Col(
                    kpi_card(
                        "Net User Change",
                        kpis.get("net_user_change", 0),
                        "info" if kpis.get("net_user_change", 0) >= 0 else "danger",
                    ),
                    md=2,
                ),
            ], className="mb-4"),

            # ======================
            # KPI ROW — DEVICES
            # ======================
            dbc.Row([
                dbc.Col(kpi_card("Total Devices", kpis.get("total_devices", 0)), md=2),
                dbc.Col(kpi_card("Devices Added", kpis.get("devices_added", 0), "success"), md=2),
                dbc.Col(kpi_card("Devices Retired", kpis.get("devices_retired", 0), "warning"), md=2),
                dbc.Col(
                    kpi_card(
                        "Net Device Change",
                        kpis.get("net_device_change", 0),
                        "success" if kpis.get("net_device_change", 0) >= 0 else "warning",
                    ),
                    md=2,
                ),
            ], className="mb-4"),

            # ======================
            # Risk Posture Banner
            # ======================
            dbc.Alert(
                f"Overall Risk Posture: "
                f"{risk.get('overall', 'unknown').upper()} — "
                f"{risk.get('summary', 'No summary available')}",
                color="success" if risk.get("overall") == "low" else "warning",
                className="mb-4",
            ),

            html.Hr(),

            # ======================
            # Identity Changes (Summary)
            # ======================
            html.H4("Identity & Access Changes"),
            html.Ul(
                [html.Li(e) for e in identity_events]
                if identity_events
                else [html.Li("No identity-related changes recorded.")]
            ),

            dbc.Row([
                dbc.Col(
                    simple_table(
                        "Users Joined",
                        users_joined,
                        "No users joined this period.",
                    ),
                    md=6,
                ),
                dbc.Col(
                    simple_table(
                        "Users Departed",
                        users_departed,
                        "No users departed this period.",
                    ),
                    md=6,
                ),
            ]),

            html.Hr(),

            # ======================
            # Asset Changes (Summary)
            # ======================
            html.H4("Endpoint & Asset Changes"),
            html.Ul(
                [html.Li(e) for e in asset_events]
                if asset_events
                else [html.Li("No asset-related changes recorded.")]
            ),

            dbc.Row([
                dbc.Col(
                    simple_table(
                        "Devices Added",
                        devices_added,
                        "No devices added this period.",
                    ),
                    md=6,
                ),
                dbc.Col(
                    simple_table(
                        "Devices Retired",
                        devices_retired,
                        "No devices retired this period.",
                    ),
                    md=6,
                ),
            ]),

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
