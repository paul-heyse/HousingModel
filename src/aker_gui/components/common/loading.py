"""
Loading state components for Aker Property Model GUI.

This module provides reusable loading indicators and progress bars
for consistent loading states across dashboards.
"""

from __future__ import annotations

from typing import Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_loading_spinner(
    message: str = "Loading...",
    size: str = "md",
    color: str = "primary",
) -> html.Div:
    """
    Create a loading spinner component.

    Args:
        message: Loading message to display
        size: Size of spinner (sm, md, lg)
        color: Bootstrap color class

    Returns:
        Loading spinner component
    """
    spinner_class = f"spinner-border spinner-border-{size} text-{color}"

    return html.Div([
        html.Div([
            html.Div(className=spinner_class, role="status"),
        ], className="d-flex justify-content-center mb-2"),
        html.P(message, className=f"text-{color} text-center"),
    ], className="loading-container p-4 text-center")


def create_progress_bar(
    value: int = 0,
    max_value: int = 100,
    label: Optional[str] = None,
    animated: bool = True,
    striped: bool = True,
    color: str = "primary",
    show_percentage: bool = True,
) -> dbc.Progress:
    """
    Create a progress bar component.

    Args:
        value: Current progress value
        max_value: Maximum progress value
        label: Optional label to display
        animated: Whether to animate the progress bar
        striped: Whether to show stripes
        color: Bootstrap color class
        show_percentage: Whether to show percentage text

    Returns:
        Progress bar component
    """
    percentage = (value / max_value) * 100 if max_value > 0 else 0

    progress_bar = dbc.Progress(
        value=value,
        max=max_value,
        animated=animated,
        striped=striped,
        color=color,
        className="mb-2",
    )

    if label or show_percentage:
        label_text = []
        if label:
            label_text.append(label)
        if show_percentage:
            label_text.append(f"{percentage:.1f}%")

        return html.Div([
            progress_bar,
            html.Small(" ".join(label_text), className="text-muted"),
        ])
    else:
        return progress_bar


def create_skeleton_loader(
    lines: int = 3,
    height: str = "1rem",
    className: str = "",
) -> html.Div:
    """
    Create a skeleton loader for content placeholders.

    Args:
        lines: Number of skeleton lines
        height: Height of each line
        className: Additional CSS classes

    Returns:
        Skeleton loader component
    """
    skeleton_lines = []
    for i in range(lines):
        skeleton_lines.append(
            html.Div(
                className=f"placeholder-glow {className}",
                style={"height": height, "marginBottom": "0.5rem"}
            )
        )

    return html.Div(skeleton_lines)


def create_loading_overlay(
    message: str = "Loading...",
    show_progress: bool = False,
    progress_value: int = 0,
) -> html.Div:
    """
    Create a full-screen loading overlay.

    Args:
        message: Loading message
        show_progress: Whether to show progress bar
        progress_value: Current progress value

    Returns:
        Loading overlay component
    """
    overlay = html.Div([
        html.Div([
            html.I(className="fas fa-spinner fa-spin fa-3x text-primary mb-3"),
            html.H4(message, className="text-primary mb-3"),
        ], className="text-center"),
    ], className="loading-overlay d-flex align-items-center justify-content-center")

    if show_progress:
        overlay.children.append(
            create_progress_bar(
                value=progress_value,
                animated=True,
                color="primary",
            )
        )

    return overlay


def create_data_loading_indicator(
    data_type: str,
    show_details: bool = False,
) -> html.Div:
    """
    Create a loading indicator for specific data types.

    Args:
        data_type: Type of data being loaded
        show_details: Whether to show detailed loading info

    Returns:
        Data loading indicator component
    """
    return html.Div([
        html.Div([
            html.I(className="fas fa-database fa-2x text-info mb-2"),
            html.H6(f"Loading {data_type}...", className="text-info"),
        ], className="text-center"),

        html.Div([
            create_loading_spinner(f"Fetching {data_type.lower()} data...", size="sm"),
        ], className="mt-2"),

        # Optional detailed info
        html.Div([
            html.Small("Connecting to data sources...", className="text-muted"),
            html.Small("Processing and validating data...", className="text-muted"),
            html.Small("Preparing visualization...", className="text-muted"),
        ], className="mt-3", style={"display": "none"} if not show_details else {}),
    ], className="data-loading-indicator p-4 border rounded bg-light")


def create_chart_loading_state(
    chart_type: str = "Chart",
    height: str = "300px",
) -> html.Div:
    """
    Create a loading state for chart components.

    Args:
        chart_type: Type of chart being loaded
        height: Height of the loading container

    Returns:
        Chart loading state component
    """
    return html.Div([
        create_loading_spinner(f"Loading {chart_type.lower()}...", size="md"),
    ], className="chart-loading-state d-flex align-items-center justify-content-center",
       style={"height": height, "border": "1px dashed #ddd", "borderRadius": "4px"})


def create_table_loading_state(
    rows: int = 5,
    columns: int = 4,
) -> html.Div:
    """
    Create a loading state for table components.

    Args:
        rows: Number of skeleton rows
        columns: Number of skeleton columns

    Returns:
        Table loading state component
    """
    header_row = html.Tr([
        html.Th(create_skeleton_loader(1, "1rem"), className="placeholder")
        for _ in range(columns)
    ])

    data_rows = []
    for _ in range(rows):
        data_rows.append(
            html.Tr([
                html.Td(create_skeleton_loader(1, "0.8rem"), className="placeholder")
                for _ in range(columns)
            ])
        )

    return html.Div([
        dbc.Table([
            html.Thead(header_row),
            html.Tbody(data_rows),
        ], bordered=True, hover=True),
    ], className="table-loading-state")


def register_loading_callbacks(app) -> None:
    """Register callbacks for loading state interactions."""

    @app.callback(
        dash.Output("loading-overlay", "style"),
        dash.Input("data-loading-trigger", "n_clicks"),
        prevent_initial_call=True,
    )
    def show_loading_overlay(n_clicks):
        """Show loading overlay when data loading is triggered."""
        if n_clicks:
            return {"display": "flex", "position": "fixed", "top": "0", "left": "0",
                   "width": "100%", "height": "100%", "backgroundColor": "rgba(0,0,0,0.5)",
                   "zIndex": "9999"}
        return {"display": "none"}
