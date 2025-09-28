"""
Error handling and empty state components for Risk Panel dashboard.

This module provides user-friendly error states and empty state handling
for the Risk Panel dashboard.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_error_state(
    error_type: str,
    message: str,
    details: Optional[str] = None,
    action_text: Optional[str] = None,
    action_callback: Optional[str] = None,
) -> html.Div:
    """
    Create an error state component.

    Args:
        error_type: Type of error (api_error, data_unavailable, etc.)
        message: Main error message
        details: Optional detailed error information
        action_text: Optional action button text
        action_callback: Optional callback ID for action button

    Returns:
        Dash HTML component for error state
    """
    error_icon = get_error_icon(error_type)

    content = [
        html.Div([
            html.I(className=f"fas {error_icon} fa-3x text-danger mb-3"),
            html.H5(message, className="text-danger"),
        ], className="text-center mb-3"),
    ]

    if details:
        content.append(
            html.Div([
                html.Small(details, className="text-muted"),
            ], className="text-center mb-3")
        )

    if action_text and action_callback:
        content.append(
            html.Div([
                dbc.Button(
                    action_text,
                    id=action_callback,
                    color="primary",
                    className="mt-3",
                ),
            ], className="text-center")
        )

    return html.Div(
        content,
        className="error-state p-4 border border-danger rounded bg-light",
    )


def create_empty_state(
    title: str,
    message: str,
    icon: str = "fas fa-chart-bar",
    action_text: Optional[str] = None,
    action_callback: Optional[str] = None,
) -> html.Div:
    """
    Create an empty state component.

    Args:
        title: Empty state title
        message: Empty state message
        icon: Icon class for the empty state
        action_text: Optional action button text
        action_callback: Optional callback ID for action button

    Returns:
        Dash HTML component for empty state
    """
    content = [
        html.Div([
            html.I(className=f"{icon} fa-3x text-muted mb-3"),
            html.H5(title, className="text-muted"),
            html.P(message, className="text-muted"),
        ], className="text-center"),
    ]

    if action_text and action_callback:
        content.append(
            html.Div([
                dbc.Button(
                    action_text,
                    id=action_callback,
                    color="primary",
                    className="mt-3",
                ),
            ], className="text-center")
        )

    return html.Div(
        content,
        className="empty-state p-4 border border-secondary rounded bg-light",
    )


def create_loading_state(
    message: str = "Loading data...",
    show_progress: bool = True,
) -> html.Div:
    """
    Create a loading state component.

    Args:
        message: Loading message to display
        show_progress: Whether to show progress bar

    Returns:
        Dash HTML component for loading state
    """
    content = [
        html.Div([
            html.I(className="fas fa-spinner fa-spin fa-2x text-primary mb-3"),
            html.H6(message, className="text-primary"),
        ], className="text-center"),
    ]

    if show_progress:
        content.append(
            dbc.Progress(
                value=50,
                striped=True,
                animated=True,
                className="mt-3",
            )
        )

    return html.Div(
        content,
        className="loading-state p-4 text-center",
    )


def get_error_icon(error_type: str) -> str:
    """
    Get appropriate icon for error type.

    Args:
        error_type: Type of error

    Returns:
        FontAwesome icon class
    """
    icon_map = {
        "api_error": "fa-exclamation-triangle",
        "data_unavailable": "fa-database",
        "network_error": "fa-wifi",
        "permission_error": "fa-lock",
        "validation_error": "fa-times-circle",
        "timeout_error": "fa-clock",
    }

    return icon_map.get(error_type, "fa-exclamation-triangle")


def create_peril_unavailable_state(peril: str, region: str) -> html.Div:
    """
    Create empty state for unavailable peril data.

    Args:
        peril: Name of the unavailable peril
        region: Region/Market where data is unavailable

    Returns:
        HTML component for unavailable peril state
    """
    return create_empty_state(
        title=f"{peril.title()} Data Unavailable",
        message=f"No {peril.title()} hazard data is available for {region} at the selected vintage. This peril may not be applicable to the current analysis or data may be pending refresh.",
        icon="fas fa-exclamation-triangle",
        action_text="Refresh Data",
        action_callback="refresh-peril-data-btn",
    )


def create_scenario_error_state(error_message: str, retry_callback: str) -> html.Div:
    """
    Create error state for scenario calculation failures.

    Args:
        error_message: Error message to display
        retry_callback: Callback ID for retry button

    Returns:
        HTML component for scenario error state
    """
    return create_error_state(
        error_type="validation_error",
        message="Scenario Calculation Failed",
        details=error_message,
        action_text="Retry Calculation",
        action_callback=retry_callback,
    )


def create_map_error_state(error_type: str, retry_callback: str) -> html.Div:
    """
    Create error state for map loading failures.

    Args:
        error_type: Type of map error
        retry_callback: Callback ID for retry button

    Returns:
        HTML component for map error state
    """
    error_messages = {
        "network_error": "Unable to load map tiles. Please check your internet connection.",
        "data_unavailable": "Map data is currently unavailable for this region.",
        "permission_error": "Insufficient permissions to access map data.",
        "timeout_error": "Map loading timed out. Please try again.",
    }

    message = error_messages.get(error_type, "An error occurred while loading the map.")

    return create_error_state(
        error_type=error_type,
        message="Map Loading Error",
        details=message,
        action_text="Retry Loading",
        action_callback=retry_callback,
    )


def create_export_error_state(error_message: str, retry_callback: str) -> html.Div:
    """
    Create error state for export failures.

    Args:
        error_message: Error message to display
        retry_callback: Callback ID for retry button

    Returns:
        HTML component for export error state
    """
    return create_error_state(
        error_type="data_unavailable",
        message="Export Generation Failed",
        details=error_message,
        action_text="Retry Export",
        action_callback=retry_callback,
    )


def register_error_state_callbacks(app: dash.Dash) -> None:
    """Register callbacks for error state interactions."""

    @app.callback(
        dash.Output("error-state-container", "children"),
        dash.Input("retry-error-btn", "n_clicks"),
        dash.State("error-state-data", "data"),
        prevent_initial_call=True,
    )
    def handle_error_retry(n_clicks, error_data):
        """Handle error retry button clicks."""
        if n_clicks and error_data:
            # This would normally trigger the retry logic
            # For now, return a loading state
            return create_loading_state("Retrying operation...")

        return dash.no_update
