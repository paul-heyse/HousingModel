"""
Common card components for Aker Property Model GUI.

This module provides reusable card components for displaying metrics,
summaries, and other content consistently across dashboards.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_metric_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    color: str = "primary",
    trend: Optional[Dict[str, Any]] = None,
    size: str = "md",
) -> dbc.Card:
    """
    Create a metric display card.

    Args:
        title: Card title
        value: Main metric value to display
        subtitle: Optional subtitle text
        icon: Optional FontAwesome icon class
        color: Bootstrap color class
        trend: Optional trend data with direction and value
        size: Card size (sm, md, lg)

    Returns:
        Bootstrap card component
    """
    card_body = []

    # Header with icon and title
    header_content = []
    if icon:
        header_content.append(html.I(className=f"{icon} me-2"))
    header_content.append(title)

    card_body.append(
        dbc.CardHeader(header_content, className=f"bg-{color} text-white")
    )

    # Main content
    content = []

    # Value display
    value_element = html.H3(value, className="card-title mb-2")
    content.append(value_element)

    # Trend indicator
    if trend:
        trend_direction = trend.get("direction", "neutral")
        trend_value = trend.get("value", 0)

        if trend_direction == "up":
            trend_icon = "fas fa-arrow-up text-success"
            trend_class = "text-success"
        elif trend_direction == "down":
            trend_icon = "fas fa-arrow-down text-danger"
            trend_class = "text-danger"
        else:
            trend_icon = "fas fa-minus text-muted"
            trend_class = "text-muted"

        content.append(
            html.Div([
                html.I(className=trend_icon, style={"marginRight": "5px"}),
                html.Small(f"{trend_value:+.1f}%", className=trend_class),
            ], className="mb-2")
        )

    # Subtitle
    if subtitle:
        content.append(html.P(subtitle, className="card-text text-muted"))

    card_body.append(dbc.CardBody(content))

    return dbc.Card(card_body, className=f"mb-3")


def create_summary_card(
    title: str,
    items: List[Dict[str, Any]],
    color: str = "light",
    size: str = "md",
) -> dbc.Card:
    """
    Create a summary card with multiple data items.

    Args:
        title: Card title
        items: List of items with label and value
        color: Bootstrap color class
        size: Card size (sm, md, lg)

    Returns:
        Bootstrap card component
    """
    content = []

    for item in items:
        label = item.get("label", "")
        value = item.get("value", "")
        icon = item.get("icon")

        item_content = []

        if icon:
            item_content.append(html.I(className=f"{icon} me-2"))

        item_content.append(html.Small(label + ": ", className="text-muted"))
        item_content.append(html.Span(value, className="fw-bold"))

        content.append(html.Div(item_content, className="mb-2"))

    return dbc.Card([
        dbc.CardHeader(title, className=f"bg-{color}"),
        dbc.CardBody(content),
    ], className="mb-3")


def create_status_card(
    title: str,
    status: str,
    details: Optional[str] = None,
    color: str = "success",
) -> dbc.Card:
    """
    Create a status indicator card.

    Args:
        title: Card title
        status: Status text to display
        details: Optional detailed information
        color: Bootstrap color class

    Returns:
        Bootstrap card component
    """
    status_icon = get_status_icon(status)

    content = [
        html.Div([
            html.I(className=f"fas {status_icon} fa-2x mb-2"),
            html.H5(status, className=f"text-{color}"),
        ], className="text-center"),
    ]

    if details:
        content.append(html.P(details, className="text-muted text-center"))

    return dbc.Card([
        dbc.CardBody(content),
    ], className="text-center mb-3")


def create_action_card(
    title: str,
    description: str,
    action_text: str,
    action_callback: str,
    icon: Optional[str] = None,
    color: str = "primary",
) -> dbc.Card:
    """
    Create an action card with button.

    Args:
        title: Card title
        description: Card description
        action_text: Text for the action button
        action_callback: Callback ID for the button
        icon: Optional icon for the card
        color: Bootstrap color class

    Returns:
        Bootstrap card component
    """
    content = []

    # Header with icon
    header_content = []
    if icon:
        header_content.append(html.I(className=f"{icon} me-2"))
    header_content.append(title)

    content.append(dbc.CardHeader(header_content))

    # Body with description and action
    body_content = [
        html.P(description, className="card-text mb-3"),
        dbc.Button(
            action_text,
            id=action_callback,
            color=color,
            className="w-100",
        ),
    ]

    content.append(dbc.CardBody(body_content))

    return dbc.Card(content, className="mb-3")


def get_status_icon(status: str) -> str:
    """Get appropriate icon for status."""
    status_icons = {
        "success": "fa-check-circle",
        "warning": "fa-exclamation-triangle",
        "error": "fa-times-circle",
        "info": "fa-info-circle",
        "loading": "fa-spinner fa-spin",
    }

    return status_icons.get(status.lower(), "fa-info-circle")


def create_loading_card(message: str = "Loading...") -> dbc.Card:
    """Create a loading state card."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-spinner fa-spin fa-2x text-primary mb-3"),
                html.H5(message, className="text-primary"),
            ], className="text-center"),
        ]),
    ], className="mb-3")


def create_error_card(
    message: str,
    details: Optional[str] = None,
    retry_callback: Optional[str] = None,
) -> dbc.Card:
    """Create an error state card."""
    content = [
        html.Div([
            html.I(className="fas fa-exclamation-triangle fa-2x text-danger mb-3"),
            html.H5(message, className="text-danger"),
        ], className="text-center mb-3"),
    ]

    if details:
        content.append(html.P(details, className="text-muted text-center"))

    if retry_callback:
        content.append(
            html.Div([
                dbc.Button(
                    "Retry",
                    id=retry_callback,
                    color="primary",
                    className="mt-3",
                ),
            ], className="text-center")
        )

    return dbc.Card([
        dbc.CardBody(content),
    ], className="mb-3")


def create_info_card(
    title: str,
    content: str,
    icon: Optional[str] = None,
    color: str = "info",
) -> dbc.Card:
    """Create an informational card."""
    header_content = []
    if icon:
        header_content.append(html.I(className=f"{icon} me-2"))
    header_content.append(title)

    return dbc.Card([
        dbc.CardHeader(header_content, className=f"bg-{color}"),
        dbc.CardBody([
            html.P(content, className="card-text"),
        ]),
    ], className="mb-3")
