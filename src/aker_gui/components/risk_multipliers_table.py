"""
Risk multipliers table component for Risk Panel dashboard.

This module provides the interactive table showing risk multipliers
and their impact on exit cap rates and contingencies.
"""

from __future__ import annotations

from typing import Dict, List

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_risk_multipliers_table(
    multipliers_data: List[Dict[str, any]] = None,
) -> html.Div:
    """
    Create the risk multipliers table component.

    Args:
        multipliers_data: List of multiplier data with peril information

    Returns:
        Dash HTML component containing the multipliers table
    """
    if multipliers_data is None:
        multipliers_data = get_placeholder_multipliers_data()

    # Create table data
    table_rows = []
    for multiplier in multipliers_data:
        table_rows.append(
            html.Tr([
                html.Td(multiplier["peril"].title()),
                html.Td(f"{multiplier['severity_idx']}/100"),
                html.Td(f"{multiplier['base_multiplier']:.3f}"),
                html.Td(f"{multiplier['scenario_multiplier']:.3f}"),
                html.Td([
                    html.Span(
                        f"{multiplier['delta']:+.3f}",
                        className="badge bg-" + get_delta_badge_class(multiplier['delta']),
                    ),
                ]),
            ])
        )

    return html.Div([
        dbc.Table([
            html.Thead(
                html.Tr([
                    html.Th("Peril"),
                    html.Th("Severity Index"),
                    html.Th("Base Multiplier"),
                    html.Th("Scenario Multiplier"),
                    html.Th("Δ"),
                ])
            ),
            html.Tbody(table_rows),
        ], bordered=True, hover=True, responsive=True, className="mb-3"),

        # Table summary
        html.Div([
            html.Small([
                "Total Impact: ",
                html.Span("-15 bps exit cap, +2.5% contingency", className="text-muted"),
            ]),
        ]),
    ])


def get_placeholder_multipliers_data() -> List[Dict[str, any]]:
    """Get placeholder multipliers data for development."""
    return [
        {
            "peril": "wildfire",
            "severity_idx": 75,
            "base_multiplier": 0.980,
            "scenario_multiplier": 0.985,
            "delta": 0.005,
        },
        {
            "peril": "hail",
            "severity_idx": 45,
            "base_multiplier": 0.995,
            "scenario_multiplier": 0.992,
            "delta": -0.003,
        },
        {
            "peril": "snow_load",
            "severity_idx": 60,
            "base_multiplier": 0.990,
            "scenario_multiplier": 0.988,
            "delta": -0.002,
        },
        {
            "peril": "flood",
            "severity_idx": 30,
            "base_multiplier": 1.000,
            "scenario_multiplier": 1.000,
            "delta": 0.000,
        },
        {
            "peril": "water_stress",
            "severity_idx": 80,
            "base_multiplier": 0.970,
            "scenario_multiplier": 0.975,
            "delta": 0.005,
        },
    ]


def get_delta_badge_class(delta: float) -> str:
    """Get Bootstrap badge class for delta values."""
    if delta > 0:
        return "success"
    elif delta < 0:
        return "danger"
    else:
        return "secondary"


def create_impact_summary_cards(
    exit_cap_delta: float = -15,
    contingency_delta: float = 2.5,
) -> html.Div:
    """Create impact summary cards."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Exit Cap Impact", className="card-title text-center"),
                        html.H3(
                            f"{exit_cap_delta:+.0f} bps",
                            className=f"card-text text-center {'text-danger' if exit_cap_delta < 0 else 'text-success'}",
                        ),
                        html.P("Basis point adjustment", className="text-center text-muted"),
                    ]),
                ]),
            ], md=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Contingency Impact", className="card-title text-center"),
                        html.H3(
                            f"{contingency_delta:+.1f}%",
                            className=f"card-text text-center {'text-warning' if contingency_delta > 0 else 'text-success'}",
                        ),
                        html.P("Percentage adjustment", className="text-center text-muted"),
                    ]),
                ]),
            ], md=6),
        ]),
    ])


def register_table_callbacks(app: dash.Dash) -> None:
    """Register callbacks for the risk multipliers table."""

    @app.callback(
        dash.Output("multipliers-table-container", "children"),
        dash.Input("apply-scenario-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def update_multipliers_table(n_clicks):
        """Update multipliers table when scenario is applied."""
        # This would normally fetch real data from the API
        # For now, return the table component
        return create_risk_multipliers_table()

    @app.callback(
        dash.Output("exit-cap-impact", "children"),
        dash.Output("contingency-impact", "children"),
        dash.Input("apply-scenario-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def update_impact_cards(n_clicks):
        """Update impact summary cards when scenario is applied."""
        # This would normally fetch real impact data
        # For now, return placeholder values
        return "-15 bps", "+2.5%"
