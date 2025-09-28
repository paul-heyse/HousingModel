"""
Data vintage banner component for Market Scorecard dashboard.

This module provides the data vintage banner with freshness indicators,
last update timestamps, and manual refresh controls.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from aker_core.config import Settings


def create_data_vintage_banner(
    vintage_data: Dict[str, any] = None,
    settings: Optional[Settings] = None,
) -> html.Div:
    """
    Create the data vintage banner component.

    Args:
        vintage_data: Dictionary with data vintage information
        settings: Application settings

    Returns:
        Dash HTML component containing the vintage banner
    """
    if settings is None:
        # Create a minimal settings object for testing
        class MinimalSettings:
            debug = True
        settings = MinimalSettings()

    if vintage_data is None:
        vintage_data = {}

    # Get freshness status
    freshness_status = get_freshness_status(vintage_data)

    banner = html.Div([
        dbc.Row([
            # Left side - Data vintage info
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-database me-2"),
                    html.Span("Data Vintage: ", className="fw-bold"),
                    html.Span(
                        vintage_data.get("vintage", "Unknown"),
                        id="data-vintage-text",
                    ),
                ]),
            ], md=4),

            # Center - Last update info
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-clock me-2"),
                    html.Span("Last Updated: ", className="fw-bold"),
                    html.Span(
                        vintage_data.get("last_updated", "Never"),
                        id="last-updated-text",
                    ),
                ]),
            ], md=4),

            # Right side - Refresh controls
            dbc.Col([
                html.Div([
                    # Freshness indicator
                    html.Div([
                        html.I(
                            className=f"fas fa-circle me-2 {freshness_status['icon_class']}",
                            style={"color": freshness_status["color"]},
                        ),
                        html.Span(
                            freshness_status["status_text"],
                            className=f"badge bg-{freshness_status['badge_class']}",
                        ),
                    ], className="d-flex align-items-center"),

                    # Refresh button
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-sync-alt me-1"), "Refresh"],
                            id="refresh-data-btn",
                            size="sm",
                            color="outline-primary",
                            className="ms-2",
                        ),
                    ], className="d-flex align-items-center justify-content-end"),
                ], className="d-flex align-items-center justify-content-between"),
            ], md=4),
        ], className="align-items-center"),

        # Progress bar for refresh operations
        dbc.Progress(
            id="refresh-progress",
            value=0,
            striped=True,
            animated=True,
            className="mt-2",
            style={"display": "none"},
        ),

        # Refresh status message
        html.Div(
            id="refresh-status",
            className="mt-2",
            style={"display": "none"},
        ),
    ], className="data-vintage-banner p-3 mb-4 border rounded")

    return banner


def get_freshness_status(vintage_data: Dict[str, any]) -> Dict[str, any]:
    """
    Determine data freshness status based on vintage information.

    Args:
        vintage_data: Dictionary with vintage and update information

    Returns:
        Dictionary with freshness status information
    """
    last_updated_str = vintage_data.get("last_updated", "")
    vintage = vintage_data.get("vintage", "")

    # Default status
    status = {
        "icon_class": "text-muted",
        "color": "#6c757d",
        "badge_class": "secondary",
        "status_text": "Unknown",
    }

    if not last_updated_str or last_updated_str == "Never":
        return status

    try:
        # Parse last updated timestamp
        if isinstance(last_updated_str, str):
            # Try different timestamp formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
                try:
                    last_updated = datetime.strptime(last_updated_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                # If no format matches, assume it's a relative time
                if "minute" in last_updated_str.lower():
                    hours_ago = 0.1  # Less than 1 hour
                elif "hour" in last_updated_str.lower():
                    hours_ago = int(last_updated_str.split()[0])
                else:
                    hours_ago = 24  # Default to 24 hours
                last_updated = datetime.now() - timedelta(hours=hours_ago)
        else:
            last_updated = last_updated_str

        # Calculate hours since last update
        hours_ago = (datetime.now() - last_updated).total_seconds() / 3600

        if hours_ago < 1:  # Less than 1 hour
            status = {
                "icon_class": "text-success",
                "color": "#28a745",
                "badge_class": "success",
                "status_text": "Fresh",
            }
        elif hours_ago < 24:  # Less than 24 hours
            status = {
                "icon_class": "text-warning",
                "color": "#ffc107",
                "badge_class": "warning",
                "status_text": "Recent",
            }
        else:  # More than 24 hours
            status = {
                "icon_class": "text-danger",
                "color": "#dc3545",
                "badge_class": "danger",
                "status_text": "Stale",
            }

    except Exception:
        # If we can't parse the timestamp, show unknown status
        pass

    return status


def create_source_attribution(vintage_data: Dict[str, any]) -> html.Div:
    """
    Create source attribution component.

    Args:
        vintage_data: Dictionary with source information

    Returns:
        HTML component with source attribution
    """
    sources = vintage_data.get("sources", [])

    if not sources:
        return html.Div()

    source_items = []
    for source in sources:
        source_items.append(
            html.Small(
                f"{source.get('name', 'Unknown')}: {source.get('version', 'N/A')}",
                className="text-muted d-block",
            )
        )

    return html.Div([
        html.Hr(className="my-2"),
        html.Small("Data Sources:", className="text-muted fw-bold"),
        html.Div(source_items),
    ])


def register_vintage_banner_callbacks(app: dash.Dash) -> None:
    """Register callbacks for data vintage banner interactions."""

    @app.callback(
        dash.Output("refresh-progress", "style"),
        dash.Output("refresh-status", "children"),
        dash.Input("refresh-data-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_refresh_click(n_clicks):
        """Handle refresh button clicks."""
        if n_clicks:
            return (
                {"display": "block"},
                html.Div([
                    html.I(className="fas fa-spinner fa-spin me-2"),
                    html.Span("Refreshing data...", className="text-primary"),
                ])
            )
        return {"display": "none"}, ""

    @app.callback(
        dash.Output("data-vintage-text", "children"),
        dash.Output("last-updated-text", "children"),
        dash.Input("data-refresh-trigger", "n_clicks"),
        dash.State("current-vintage-data", "data"),
    )
    def update_vintage_display(n_clicks, vintage_data):
        """Update vintage display when data is refreshed."""
        if not vintage_data:
            return "Unknown", "Never"

        return (
            vintage_data.get("vintage", "Unknown"),
            vintage_data.get("last_updated", "Never"),
        )
