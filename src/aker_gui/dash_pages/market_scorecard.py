"""
Market Scorecard dashboard page for Aker Property Model GUI.

This page displays interactive maps, pillar score cards, and market analysis tools.
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from ..components.data_vintage_banner import create_data_vintage_banner, register_vintage_banner_callbacks
from ..components.map_component import create_map_component, register_map_callbacks
from ..components.pillar_cards import create_pillar_cards, register_pillar_callbacks


def create_layout() -> html.Div:
    """Create the Market Scorecard page layout."""
    return html.Div([
        # Page header
        html.H1("Market Scorecard", className="mb-4"),
        html.P("Interactive market analysis and scoring dashboard", className="text-muted"),

        # Data vintage banner
        create_data_vintage_banner(),

        # Controls row
        dbc.Row([
            dbc.Col([
                html.Label("Select Markets:"),
                dcc.Dropdown(
                    id="market-selector",
                    placeholder="Choose markets to analyze...",
                    multi=True,
                ),
            ], md=6),
            dbc.Col([
                html.Label("Data Vintage:"),
                dcc.Dropdown(
                    id="data-vintage-selector",
                    placeholder="Select data vintage...",
                ),
            ], md=3),
            dbc.Col([
                html.Label("Actions:"),
                dbc.ButtonGroup([
                    dbc.Button("Refresh Data", id="refresh-data-btn", color="primary"),
                    dbc.Button("Export", id="export-btn", color="secondary"),
                ]),
            ], md=3),
        ], className="mb-4"),

        # Main content area
        dbc.Tabs([
            dbc.Tab([
                # Map and pillar cards
                dbc.Row([
                    dbc.Col([
                        # Interactive map
                        create_map_component(),
                    ], md=8),
                    dbc.Col([
                        # Pillar score cards
                        html.H5("Pillar Scores"),
                        create_pillar_cards(),
                    ], md=4),
                ]),

                # Detailed metrics table
                html.H5("Market Metrics", className="mt-4"),
                html.Div(id="market-metrics-table"),
            ], label="Overview"),

            dbc.Tab([
                html.H5("Market Comparison"),
                html.Div("Market comparison tools - Coming Soon"),
            ], label="Comparison"),

            dbc.Tab([
                html.H5("Market Details"),
                html.Div("Detailed market analysis - Coming Soon"),
            ], label="Details"),
        ]),

        # Hidden components for data storage
        dcc.Store(id="market-data-store"),
        dcc.Store(id="selected-markets-store"),
    ])


def create_pillar_cards() -> html.Div:
    """Create the pillar score cards."""
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-home me-2"),
                "Supply Constraints",
            ]),
            dbc.CardBody([
                html.H3("4.2", id="supply-score", className="card-title"),
                html.P("0-5 Scale", className="card-text text-muted"),
                html.Div([
                    html.Small("Last updated: ", className="text-muted"),
                    html.Small(id="supply-updated", className="text-muted"),
                ]),
            ]),
        ], className="mb-3"),

        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-briefcase me-2"),
                "Innovation Jobs",
            ]),
            dbc.CardBody([
                html.H3("3.8", id="jobs-score", className="card-title"),
                html.P("0-5 Scale", className="card-text text-muted"),
                html.Div([
                    html.Small("Last updated: ", className="text-muted"),
                    html.Small(id="jobs-updated", className="text-muted"),
                ]),
            ]),
        ], className="mb-3"),

        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-city me-2"),
                "Urban Convenience",
            ]),
            dbc.CardBody([
                html.H3("4.1", id="urban-score", className="card-title"),
                html.P("0-5 Scale", className="card-text text-muted"),
                html.Div([
                    html.Small("Last updated: ", className="text-muted"),
                    html.Small(id="urban-updated", className="text-muted"),
                ]),
            ]),
        ], className="mb-3"),

        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-mountain me-2"),
                "Outdoor Access",
            ]),
            dbc.CardBody([
                html.H3("3.9", id="outdoors-score", className="card-title"),
                html.P("0-5 Scale", className="card-text text-muted"),
                html.Div([
                    html.Small("Last updated: ", className="text-muted"),
                    html.Small(id="outdoors-updated", className="text-muted"),
                ]),
            ]),
        ], className="mb-3"),

        # Overall score card
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-star me-2"),
                "Overall Score",
            ]),
            dbc.CardBody([
                html.H2("4.0", id="overall-score", className="card-title text-primary"),
                html.P("Weighted Average", className="card-text text-muted"),
                html.Div([
                    html.Small("Risk Multiplier: ", className="text-muted"),
                    html.Small("1.05", id="risk-multiplier", className="text-muted"),
                ]),
            ]),
        ]),
    ])


def register_callbacks(app: dash.Dash) -> None:
    """Register callbacks for the market scorecard page."""

    @app.callback(
        dash.Output("market-selector", "options"),
        dash.Input("market-data-store", "data")
    )
    def update_market_selector(market_data):
        """Update market selector options when data loads."""
        if not market_data:
            return []

        # This would normally come from the API
        return [
            {"label": f"{market['name']} ({market['msa_id']})", "value": market["msa_id"]}
            for market in market_data.get("markets", [])
        ]

    @app.callback(
        [dash.Output("supply-score", "children"),
         dash.Output("jobs-score", "children"),
         dash.Output("urban-score", "children"),
         dash.Output("outdoors-score", "children"),
         dash.Output("overall-score", "children")],
        [dash.Input("market-selector", "value")]
    )
    def update_pillar_scores(selected_markets):
        """Update pillar scores when markets are selected."""
        if not selected_markets:
            return "N/A", "N/A", "N/A", "N/A", "N/A"

        # This would normally fetch real data from the API
        # For now, return placeholder data
        return "4.2", "3.8", "4.1", "3.9", "4.0"

    # Register component callbacks
    register_map_callbacks(app)
    register_pillar_callbacks(app)
    register_vintage_banner_callbacks(app)
