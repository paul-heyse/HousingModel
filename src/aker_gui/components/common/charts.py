"""
Common chart components for Aker Property Model GUI.

This module provides reusable chart components using Plotly for
consistent visualization across dashboards.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
from dash import dcc, html


def create_line_chart(
    data: List[Dict[str, Any]],
    x_column: str,
    y_column: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    height: int = 300,
) -> dcc.Graph:
    """
    Create a line chart using Plotly.

    Args:
        data: List of data points
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        height: Chart height in pixels

    Returns:
        Plotly graph component
    """
    x_values = [item.get(x_column) for item in data]
    y_values = [item.get(y_column) for item in data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name=y_column,
        line=dict(color='#007bff', width=2),
        marker=dict(size=6),
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_white',
    )

    return dcc.Graph(figure=fig, style={"height": f"{height}px"})


def create_bar_chart(
    data: List[Dict[str, Any]],
    x_column: str,
    y_column: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    orientation: str = "v",
    height: int = 300,
) -> dcc.Graph:
    """
    Create a bar chart using Plotly.

    Args:
        data: List of data points
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        orientation: Chart orientation ('v' for vertical, 'h' for horizontal)
        height: Chart height in pixels

    Returns:
        Plotly graph component
    """
    x_values = [item.get(x_column) for item in data]
    y_values = [item.get(y_column) for item in data]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_values if orientation == "v" else y_values,
        y=y_values if orientation == "v" else x_values,
        orientation=orientation,
        marker=dict(color='#28a745'),
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_white',
    )

    return dcc.Graph(figure=fig, style={"height": f"{height}px"})


def create_pie_chart(
    data: List[Dict[str, Any]],
    labels_column: str,
    values_column: str,
    title: str = "",
    height: int = 300,
) -> dcc.Graph:
    """
    Create a pie chart using Plotly.

    Args:
        data: List of data points
        labels_column: Column name for labels
        values_column: Column name for values
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly graph component
    """
    labels = [item.get(labels_column) for item in data]
    values = [item.get(values_column) for item in data]

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1']),
    ))

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_white',
    )

    return dcc.Graph(figure=fig, style={"height": f"{height}px"})


def create_histogram(
    data: List[float],
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    bins: int = 30,
    height: int = 300,
) -> dcc.Graph:
    """
    Create a histogram using Plotly.

    Args:
        data: List of numeric values
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        bins: Number of histogram bins
        height: Chart height in pixels

    Returns:
        Plotly graph component
    """
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=data,
        nbinsx=bins,
        marker=dict(color='#6f42c1'),
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_white',
    )

    return dcc.Graph(figure=fig, style={"height": f"{height}px"})


def create_scatter_plot(
    data: List[Dict[str, Any]],
    x_column: str,
    y_column: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    color_column: Optional[str] = None,
    height: int = 300,
) -> dcc.Graph:
    """
    Create a scatter plot using Plotly.

    Args:
        data: List of data points
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        color_column: Optional column for color coding
        height: Chart height in pixels

    Returns:
        Plotly graph component
    """
    x_values = [item.get(x_column) for item in data]
    y_values = [item.get(y_column) for item in data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers',
        marker=dict(
            size=8,
            color=item.get(color_column) if color_column else '#007bff',
            showscale=color_column is not None,
        ),
        text=[f"{item.get('label', '')}" for item in data],
        hovertemplate="%{text}<br>%{x}<br>%{y}<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_white',
    )

    return dcc.Graph(figure=fig, style={"height": f"{height}px"})


def create_heatmap(
    data: List[List[float]],
    x_labels: List[str],
    y_labels: List[str],
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    height: int = 300,
) -> dcc.Graph:
    """
    Create a heatmap using Plotly.

    Args:
        data: 2D list of values
        x_labels: Labels for x-axis
        y_labels: Labels for y-axis
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        height: Chart height in pixels

    Returns:
        Plotly graph component
    """
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=data,
        x=x_labels,
        y=y_labels,
        colorscale='Viridis',
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        template='plotly_white',
    )

    return dcc.Graph(figure=fig, style={"height": f"{height}px"})


def create_gauge_chart(
    value: float,
    title: str = "",
    min_value: float = 0,
    max_value: float = 100,
    height: int = 200,
) -> dcc.Graph:
    """
    Create a gauge chart using Plotly.

    Args:
        value: Current value
        title: Chart title
        min_value: Minimum value
        max_value: Maximum value
        height: Chart height in pixels

    Returns:
        Plotly graph component
    """
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_value, max_value]},
            'bar': {'color': '#007bff'},
            'steps': [
                {'range': [min_value, max_value * 0.5], 'color': '#dc3545'},
                {'range': [max_value * 0.5, max_value * 0.8], 'color': '#ffc107'},
                {'range': [max_value * 0.8, max_value], 'color': '#28a745'},
            ],
        }
    ))

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        template='plotly_white',
    )

    return dcc.Graph(figure=fig, style={"height": f"{height}px"})
