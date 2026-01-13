
import dash_bootstrap_components as dbc
from dash import html

def simple_table(title, rows, empty_message="None"):
    if not rows:
        rows = [empty_message]

    return dbc.Card(
        [
            dbc.CardHeader(title),
            dbc.CardBody(
                html.Ul(
                    [html.Li(r) for r in rows],
                    className="mb-0"
                )
            ),
        ],
        className="mb-3",
    )
