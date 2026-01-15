import dash_bootstrap_components as dbc
from dash import html


def simple_table(title: str, rows: list, empty_text: str):
    return dbc.Card(
        [
            dbc.CardHeader(html.H5(title)),
            dbc.CardBody(
                html.Table(
                    [
                        html.Thead(
                            html.Tr([html.Th("Item")])
                        ),
                        html.Tbody(
                            [html.Tr([html.Td(r)]) for r in rows]
                            if rows
                            else [html.Tr([html.Td(empty_text)])]
                        )
                    ],
                    className="table table-striped table-bordered"
                )
            )
        ],
        className="mb-4"
    )
