"""
Pillar score cards component for Market Scorecard dashboard.

This module provides the four pillar score cards (Supply, Jobs, Urban, Outdoors)
with real-time data binding and interactive features.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from aker_core.config import Settings


def create_pillar_cards(
    pillar_data: Dict[str, Dict[str, any]] = None,
    selected_msa: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> html.Div:
    """
    Create the four pillar score cards.

    Args:
        pillar_data: Dictionary with pillar scores and metadata
        selected_msa: Currently selected MSA ID
        settings: Application settings

    Returns:
        Dash HTML component containing the pillar cards
    """
    if settings is None:
        # Create a minimal settings object for testing
        class MinimalSettings:
            debug = True
        settings = MinimalSettings()

    if pillar_data is None:
        pillar_data = {}

    # Define pillar configurations
    pillars = [
        {
            "key": "supply",
            "name": "Supply Constraints",
            "icon": "fas fa-home",
            "color": "primary",
            "description": "Topography, regulatory friction, and market elasticity",
        },
        {
            "key": "jobs",
            "name": "Innovation Jobs",
            "icon": "fas fa-briefcase",
            "color": "success",
            "description": "Tech, health, education growth and human capital",
        },
        {
            "key": "urban",
            "name": "Urban Convenience",
            "icon": "fas fa-city",
            "color": "info",
            "description": "15-minute access to amenities and transit connectivity",
        },
        {
            "key": "outdoors",
            "name": "Outdoor Access",
            "icon": "fas fa-mountain",
            "color": "warning",
            "description": "Recreation proximity, air quality, and public lands",
        },
    ]

    cards = []
    for pillar in pillars:
        pillar_key = pillar["key"]
        pillar_info = pillar_data.get(pillar_key, {})

        card = dbc.Card([
            dbc.CardHeader([
                html.I(className=f"{pillar['icon']} me-2"),
                pillar["name"],
            ], className=f"bg-{pillar['color']} text-white"),

            dbc.CardBody([
                # Score display
                html.Div([
                    html.H2(
                        f"{pillar_info.get('score', 'N/A')}",
                        id=f"{pillar_key}-score",
                        className="card-title mb-2",
                    ),
                    html.Small(
                        f"{pillar_info.get('bucket_score', 'N/A')}/5",
                        className="text-muted",
                    ),
                ]),

                # Trend indicator
                html.Div([
                    create_trend_indicator(
                        pillar_info.get("trend", 0),
                        pillar_info.get("trend_period", "1M")
                    ),
                ], className="mb-3"),

                # Description
                html.P(
                    pillar["description"],
                    className="card-text small text-muted mb-2",
                ),

                # Metadata
                html.Div([
                    html.Small([
                        "Last updated: ",
                        html.Span(
                            pillar_info.get("last_updated", "Never"),
                            id=f"{pillar_key}-last-updated",
                            className="text-muted",
                        ),
                    ]),
                ]),

                # Drill-down button
                html.Div([
                    dbc.Button(
                        "View Details",
                        id=f"{pillar_key}-drilldown-btn",
                        size="sm",
                        color=pillar["color"],
                        className="mt-2",
                    ),
                ], className="text-end"),
            ]),
        ], className="mb-3")

        cards.append(card)

    # Overall score card
    overall_data = pillar_data.get("overall", {})
    overall_card = dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-star me-2"),
            "Overall Score",
        ], className="bg-dark text-white"),

        dbc.CardBody([
            html.H1(
                f"{overall_data.get('score', 'N/A')}",
                id="overall-score",
                className="card-title text-center text-primary mb-2",
            ),
            html.P(
                f"{overall_data.get('bucket_score', 'N/A')}/5",
                className="text-center text-muted mb-3",
            ),

            # Risk multiplier
            html.Div([
                html.Small("Risk Multiplier: ", className="text-muted"),
                html.Span(
                    f"{overall_data.get('risk_multiplier', 'N/A')}",
                    id="risk-multiplier",
                    className="fw-bold",
                ),
            ], className="text-center"),

            # Score breakdown
            html.Div([
                create_score_breakdown(pillar_data),
            ], className="mt-3"),
        ]),
    ])

    cards.append(overall_card)

    return html.Div(cards, className="pillar-cards")


def create_trend_indicator(trend: float, period: str) -> html.Div:
    """
    Create a trend indicator with arrow and percentage.

    Args:
        trend: Trend value (positive = up, negative = down)
        period: Time period for the trend

    Returns:
        HTML component with trend visualization
    """
    if trend == 0:
        icon_class = "fas fa-minus text-muted"
        trend_class = "text-muted"
        trend_text = "No change"
    elif trend > 0:
        icon_class = "fas fa-arrow-up text-success"
        trend_class = "text-success"
        trend_text = f"+{trend:.1f}%"
    else:
        icon_class = "fas fa-arrow-down text-danger"
        trend_class = "text-danger"
        trend_text = f"{trend:.1f}%"

    return html.Div([
        html.I(className=icon_class, style={"marginRight": "5px"}),
        html.Small(
            f"{trend_text} ({period})",
            className=trend_class,
        ),
    ])


def create_score_breakdown(pillar_data: Dict[str, Dict[str, any]]) -> html.Div:
    """
    Create a visual breakdown of pillar contributions to overall score.

    Args:
        pillar_data: Dictionary with pillar scores

    Returns:
        HTML component with score breakdown visualization
    """
    pillars = ["supply", "jobs", "urban", "outdoors"]
    breakdown_items = []

    for pillar_key in pillars:
        pillar_info = pillar_data.get(pillar_key, {})
        score = pillar_info.get("score", 0)
        weight = pillar_info.get("weight", 0.25)  # Default weights

        contribution = score * weight

        breakdown_items.append(
            html.Div([
                html.Small(
                    f"{pillar_key.title()}: {score:.1f} × {weight:.0%} = {contribution:.1f}",
                    className="text-muted",
                ),
            ], className="mb-1")
        )

    return html.Div(breakdown_items)


def register_pillar_callbacks(app: dash.Dash) -> None:
    """Register callbacks for pillar card interactions."""

    @app.callback(
        [dash.Output("supply-score", "children"),
         dash.Output("jobs-score", "children"),
         dash.Output("urban-score", "children"),
         dash.Output("outdoors-score", "children"),
         dash.Output("overall-score", "children")],
        dash.Input("selected-msa-store", "data"),
    )
    def update_pillar_scores(selected_msa):
        """Update pillar scores when MSA selection changes."""
        if not selected_msa:
            return "N/A", "N/A", "N/A", "N/A", "N/A"

        # This would normally fetch real data from the API
        # For now, return placeholder data
        return "4.2", "3.8", "4.1", "3.9", "4.0"

    @app.callback(
        dash.Output("supply-last-updated", "children"),
        dash.Input("data-refresh-trigger", "n_clicks"),
    )
    def update_supply_timestamp(n_clicks):
        """Update timestamp when data is refreshed."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    @app.callback(
        dash.Output("supply-drilldown-modal", "is_open"),
        [dash.Input("supply-drilldown-btn", "n_clicks"),
         dash.Input("supply-drilldown-close", "n_clicks")],
        dash.State("supply-drilldown-modal", "is_open"),
    )
    def toggle_supply_drilldown(n_clicks_open, n_clicks_close, is_open):
        """Toggle supply drill-down modal."""
        if n_clicks_open or n_clicks_close:
            return not is_open
        return is_open
