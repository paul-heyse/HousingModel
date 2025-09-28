"""
Common table components for Aker Property Model GUI.

This module provides reusable table components for displaying
data consistently across dashboards.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_data_table(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    id: str,
    title: Optional[str] = None,
    sortable: bool = True,
    filterable: bool = False,
    page_size: int = 10,
    height: str = "400px",
) -> html.Div:
    """
    Create a data table component.

    Args:
        data: List of data rows
        columns: List of column definitions
        id: Component ID
        title: Optional table title
        sortable: Whether table is sortable
        filterable: Whether table has filtering
        page_size: Number of rows per page
        height: Table height

    Returns:
        Dash HTML component containing the data table
    """
    table = html.Div([
        # Table title
        html.H6(title, className="mb-3") if title else None,

        # Data table
        dbc.Table.from_dataframe(
            data=data,
            columns=columns,
            id=id,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            style={"height": height, "overflow": "auto"},
        ),
    ])

    return table


def create_summary_table(
    data: List[Dict[str, Any]],
    title: str = "Summary",
    columns: Optional[List[str]] = None,
) -> html.Div:
    """
    Create a summary table with key metrics.

    Args:
        data: List of summary data
        title: Table title
        columns: Optional column names

    Returns:
        HTML component with summary table
    """
    if columns is None:
        columns = list(data[0].keys()) if data else []

    table_rows = []
    for row_data in data:
        table_row = html.Tr([
            html.Td(row_data.get(col, ""), className="fw-bold")
            for col in columns
        ])
        table_rows.append(table_row)

    return html.Div([
        html.H6(title, className="mb-3"),
        dbc.Table([
            html.Thead(
                html.Tr([
                    html.Th(col.replace("_", " ").title())
                    for col in columns
                ])
            ),
            html.Tbody(table_rows),
        ], bordered=True, hover=True, size="sm"),
    ])


def create_comparison_table(
    data: List[Dict[str, Any]],
    compare_columns: List[str],
    title: str = "Comparison",
) -> html.Div:
    """
    Create a comparison table with highlighting.

    Args:
        data: List of comparison data
        compare_columns: Columns to highlight differences
        title: Table title

    Returns:
        HTML component with comparison table
    """
    table_rows = []

    for row_data in data:
        table_row = html.Tr([
            html.Td(
                row_data.get(col, ""),
                className="table-success" if col in compare_columns and row_data.get(col, "") else ""
            )
            for col in row_data.keys()
        ])
        table_rows.append(table_row)

    return html.Div([
        html.H6(title, className="mb-3"),
        dbc.Table([
            html.Thead(
                html.Tr([
                    html.Th(col.replace("_", " ").title())
                    for col in data[0].keys() if data
                ])
            ),
            html.Tbody(table_rows),
        ], bordered=True, hover=True, size="sm"),
    ])


def create_exportable_table(
    data: List[Dict[str, Any]],
    columns: List[str],
    title: str = "Exportable Data",
    export_id: str = "export-table",
) -> html.Div:
    """
    Create a table with export functionality.

    Args:
        data: List of data rows
        columns: List of column names
        title: Table title
        export_id: ID for export button

    Returns:
        HTML component with table and export button
    """
    return html.Div([
        # Header with title and export button
        html.Div([
            html.H6(title, className="mb-0"),
            dbc.Button(
                [html.I(className="fas fa-download me-1"), "Export"],
                id=export_id,
                color="outline-primary",
                size="sm",
            ),
        ], className="d-flex justify-content-between align-items-center mb-3"),

        # Table
        create_data_table(data, columns, "exportable-table"),
    ])


def create_filterable_table(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    title: str = "Filterable Data",
    filter_columns: Optional[List[str]] = None,
) -> html.Div:
    """
    Create a table with filtering capabilities.

    Args:
        data: List of data rows
        columns: List of column definitions
        title: Table title
        filter_columns: Columns that can be filtered

    Returns:
        HTML component with table and filters
    """
    if filter_columns is None:
        filter_columns = [col["id"] for col in columns]

    filter_inputs = []
    for col in columns:
        if col["id"] in filter_columns:
            filter_inputs.append(
                dbc.Col([
                    html.Label(col["name"], className="small"),
                    dcc.Input(
                        id=f"filter-{col['id']}",
                        type="text",
                        placeholder=f"Filter {col['name']}...",
                        className="form-control form-control-sm",
                    ),
                ], md=3)
            )

    return html.Div([
        # Filters
        html.Div([
            html.H6("Filters", className="mb-2"),
            dbc.Row(filter_inputs),
        ], className="mb-3"),

        # Table
        create_data_table(data, columns, "filterable-table", title),
    ])


def create_sortable_table(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    title: str = "Sortable Data",
    default_sort: Optional[Dict[str, str]] = None,
) -> html.Div:
    """
    Create a table with sorting capabilities.

    Args:
        data: List of data rows
        columns: List of column definitions
        title: Table title
        default_sort: Default sort configuration

    Returns:
        HTML component with sortable table
    """
    return html.Div([
        html.H6(title, className="mb-3"),
        create_data_table(data, columns, "sortable-table", sortable=True),
    ])


def create_pagination_info(
    current_page: int,
    page_size: int,
    total_items: int,
) -> html.Div:
    """
    Create pagination information display.

    Args:
        current_page: Current page number (1-indexed)
        page_size: Number of items per page
        total_items: Total number of items

    Returns:
        HTML component with pagination info
    """
    start_item = (current_page - 1) * page_size + 1
    end_item = min(current_page * page_size, total_items)
    total_pages = (total_items + page_size - 1) // page_size

    return html.Div([
        html.Small(f"Showing {start_item}-{end_item} of {total_items} items", className="text-muted"),
        html.Small(f"Page {current_page} of {total_pages}", className="text-muted ms-3"),
    ], className="d-flex justify-content-between align-items-center mt-2")


def create_table_controls(
    show_search: bool = True,
    show_export: bool = True,
    show_refresh: bool = True,
    search_placeholder: str = "Search...",
) -> html.Div:
    """
    Create table control components.

    Args:
        show_search: Whether to show search input
        show_export: Whether to show export button
        show_refresh: Whether to show refresh button
        search_placeholder: Placeholder text for search

    Returns:
        HTML component with table controls
    """
    controls = []

    if show_search:
        controls.append(
            dcc.Input(
                id="table-search",
                type="text",
                placeholder=search_placeholder,
                className="form-control me-2",
                style={"width": "300px"},
            )
        )

    if show_export:
        controls.append(
            dbc.Button(
                [html.I(className="fas fa-download me-1"), "Export"],
                id="table-export-btn",
                color="outline-primary",
                size="sm",
            )
        )

    if show_refresh:
        controls.append(
            dbc.Button(
                [html.I(className="fas fa-sync-alt me-1"), "Refresh"],
                id="table-refresh-btn",
                color="outline-secondary",
                size="sm",
            )
        )

    return html.Div(controls, className="d-flex align-items-center mb-3")


def register_table_callbacks(app) -> None:
    """Register callbacks for table interactions."""

    @app.callback(
        dash.Output("filterable-table", "data"),
        dash.Input("filter-*", "value"),
    )
    def filter_table(*filter_values):
        """Filter table based on input values."""
        # This would implement actual filtering logic
        # For now, return placeholder
        return []

    @app.callback(
        dash.Output("sortable-table", "data"),
        dash.Input("sortable-table", "sort_by"),
    )
    def sort_table(sort_by):
        """Sort table based on column selection."""
        # This would implement actual sorting logic
        # For now, return placeholder
        return []
