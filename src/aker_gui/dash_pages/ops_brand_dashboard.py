from __future__ import annotations

import base64
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

import dash
from dash import dcc, html, Input, Output, State, callback, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from aker_gui.app import app
from aker_gui.components.data_vintage_banner import create_data_vintage_banner


def create_ops_brand_dashboard(asset_id: str = None) -> html.Div:
    """Create the Ops & Brand dashboard layout."""

    # Default to sample asset if none provided
    if not asset_id:
        asset_id = "AKR-123"

    return html.Div([
        # Header with breadcrumb
        dbc.Row([
            dbc.Col([
                html.H1("Ops & Brand", className="mb-3"),
                html.Nav([
                    html.Span("Assets", className="breadcrumb-link"),
                    html.Span(" → ", className="breadcrumb-separator"),
                    html.Span("Ops & Brand", className="breadcrumb-current")
                ], className="breadcrumb mb-3")
            ], width=8),
            dbc.Col([
                html.Div([
                    html.Small("Asset: ", className="text-muted"),
                    html.Strong(asset_id, className="ms-2")
                ], className="d-flex align-items-center justify-content-end")
            ], width=4)
        ]),

        # Data vintage banner
        create_data_vintage_banner(),

        # Top controls bar
        dbc.Row([
            dbc.Col([
                html.Label("Date Range:", className="form-label"),
                dcc.DatePickerRange(
                    id="ops-date-range",
                    start_date=(date.today() - timedelta(days=365)).isoformat(),
                    end_date=date.today().isoformat(),
                    display_format="YYYY-MM-DD",
                    className="mb-2"
                )
            ], width=3),
            dbc.Col([
                html.Label("Review Sources:", className="form-label"),
                dcc.Dropdown(
                    id="ops-source-filter",
                    options=[
                        {"label": "All Sources", "value": "all"},
                        {"label": "Google Reviews", "value": "google"},
                        {"label": "Yelp", "value": "yelp"},
                        {"label": "Apartments.com", "value": "apartments"},
                        {"label": "Other", "value": "other"}
                    ],
                    value="all",
                    multi=True,
                    className="mb-2"
                )
            ], width=3),
            dbc.Col([
                html.Label("Upload Reviews CSV:", className="form-label"),
                dcc.Upload(
                    id="ops-csv-upload",
                    children=html.Div([
                        "Drag and Drop or ",
                        html.A("Select CSV File")
                    ]),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "10px"
                    },
                    multiple=False
                )
            ], width=3),
            dbc.Col([
                html.Label("Download Template:", className="form-label"),
                html.A(
                    "📥 CSV Template",
                    href="/static/csv_templates/reviews_template.csv",
                    download="reviews_template.csv",
                    className="btn btn-outline-primary btn-sm mt-3"
                )
            ], width=3)
        ], className="mb-4"),

        # Main content area
        dbc.Row([
            # Left column - Charts
            dbc.Col([
                # NPS Trend Chart
                dbc.Card([
                    dbc.CardHeader("NPS Trend"),
                    dbc.CardBody([
                        dcc.Graph(id="ops-nps-chart", style={"height": "300px"})
                    ])
                ], className="mb-3"),

                # Reviews Volume & Rating Chart
                dbc.Card([
                    dbc.CardHeader("Reviews Volume & Average Rating"),
                    dbc.CardBody([
                        dcc.Graph(id="ops-reviews-chart", style={"height": "300px"})
                    ])
                ])
            ], width=6),

            # Right column - Metrics & Controls
            dbc.Col([
                # Reputation Index Gauge
                dbc.Card([
                    dbc.CardHeader("Reputation Index"),
                    dbc.CardBody([
                        html.Div([
                            html.H2(id="ops-reputation-index", className="text-center"),
                            html.Small("Current Score", className="text-muted d-block text-center")
                        ], className="reputation-gauge"),
                        html.Div([
                            html.Small("Poor", className="text-danger"),
                            html.Small("Fair", className="text-warning"),
                            html.Small("Good", className="text-info"),
                            html.Small("Excellent", className="text-success")
                        ], className="reputation-legend text-center mt-2")
                    ])
                ], className="mb-3"),

                # Pricing Rules Table
                dbc.Card([
                    dbc.CardHeader("Current Pricing Guardrails"),
                    dbc.CardBody([
                        html.Div(id="ops-pricing-rules", className="pricing-rules-table")
                    ])
                ], className="mb-3"),

                # What-if Slider
                dbc.Card([
                    dbc.CardHeader("What-if Scenario"),
                    dbc.CardBody([
                        html.Label("Adjust Reputation Index:", className="form-label"),
                        dcc.Slider(
                            id="ops-whatif-slider",
                            min=0,
                            max=100,
                            value=78,  # Default to current reputation
                            marks={i: str(i) for i in range(0, 101, 20)},
                            className="mb-3"
                        ),
                        html.Div(id="ops-whatif-preview", className="whatif-preview")
                    ])
                ])
            ], width=6)
        ]),

        # Upload Results (hidden initially)
        html.Div(id="ops-upload-results", style={"display": "none"}),

        # Loading spinner
        dcc.Loading(
            id="ops-loading",
            type="default",
            children=html.Div(id="ops-loading-placeholder")
        ),

        # Store for upload metadata
        dcc.Store(id="ops-upload-meta", storage_type="session")
    ], className="ops-brand-dashboard")


# Register the page
dash.register_page(
    "ops_brand_dashboard",
    path="/app/ops",
    title="Ops & Brand",
    name="Ops & Brand",
    layout=create_ops_brand_dashboard
)


@callback(
    Output("ops-nps-chart", "figure"),
    Output("ops-reviews-chart", "figure"),
    Output("ops-reputation-index", "children"),
    Output("ops-pricing-rules", "children"),
    Input("ops-date-range", "start_date"),
    Input("ops-date-range", "end_date"),
    Input("ops-source-filter", "value"),
    Input("ops-upload-meta", "data")
)
def update_dashboard_charts(start_date: str, end_date: str, sources: List[str], upload_data: Optional[Dict]):
    """Update dashboard charts and metrics."""

    # Sample data - in real implementation would call API
    nps_data = [
        {"date": "2024-01-01", "nps": 25},
        {"date": "2024-02-01", "nps": 30},
        {"date": "2024-03-01", "nps": 28},
        {"date": "2024-04-01", "nps": 32},
        {"date": "2024-05-01", "nps": 35},
        {"date": "2024-06-01", "nps": 33},
        {"date": "2024-07-01", "nps": 38},
        {"date": "2024-08-01", "nps": 40},
        {"date": "2024-09-01", "nps": 42},
        {"date": "2024-10-01", "nps": 45},
        {"date": "2024-11-01", "nps": 43},
        {"date": "2024-12-01", "nps": 47}
    ]

    reviews_data = [
        {"date": "2024-01-01", "rating": 4.2, "volume": 15},
        {"date": "2024-02-01", "rating": 4.1, "volume": 18},
        {"date": "2024-03-01", "rating": 4.3, "volume": 22},
        {"date": "2024-04-01", "rating": 4.0, "volume": 16},
        {"date": "2024-05-01", "rating": 4.4, "volume": 25},
        {"date": "2024-06-01", "rating": 4.2, "volume": 20},
        {"date": "2024-07-01", "rating": 4.5, "volume": 28},
        {"date": "2024-08-01", "rating": 4.3, "volume": 24},
        {"date": "2024-09-01", "rating": 4.6, "volume": 32},
        {"date": "2024-10-01", "rating": 4.4, "volume": 29},
        {"date": "2024-11-01", "rating": 4.3, "volume": 26},
        {"date": "2024-12-01", "rating": 4.5, "volume": 31}
    ]

    # NPS Trend Chart
    nps_df = pd.DataFrame(nps_data)
    nps_fig = px.line(
        nps_df,
        x="date",
        y="nps",
        title="NPS Trend Over Time",
        labels={"nps": "NPS Score", "date": "Date"}
    )
    nps_fig.update_layout(height=300)

    # Reviews Chart (dual axis)
    reviews_df = pd.DataFrame(reviews_data)
    reviews_fig = go.Figure()

    # Add volume bars
    reviews_fig.add_trace(go.Bar(
        x=reviews_df["date"],
        y=reviews_df["volume"],
        name="Review Volume",
        marker_color="lightblue",
        yaxis="y1"
    ))

    # Add rating line
    reviews_fig.add_trace(go.Scatter(
        x=reviews_df["date"],
        y=reviews_df["rating"],
        name="Average Rating",
        line=dict(color="darkblue", width=3),
        yaxis="y2"
    ))

    reviews_fig.update_layout(
        title="Reviews Volume & Average Rating",
        yaxis=dict(title="Volume", side="left"),
        yaxis2=dict(title="Rating", side="right", overlaying="y", range=[0, 5]),
        height=300
    )

    # Reputation Index (calculated from NPS and reviews)
    current_reputation = 78.5  # Would be calculated from actual data

    # Pricing Rules Table
    pricing_rules = {
        "max_concession_days": 7,
        "floor_price_pct": 5.0,
        "premium_cap_pct": 8.0
    }

    pricing_table = html.Table([
        html.Thead([
            html.Tr([
                html.Th("Metric"),
                html.Th("Current Value"),
                html.Th("Description")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td("Max Concession Days"),
                html.Td(f"{pricing_rules['max_concession_days']} days"),
                html.Td("Maximum days of rent concessions allowed")
            ]),
            html.Tr([
                html.Td("Floor Price %"),
                html.Td(f"{pricing_rules['floor_price_pct']}%"),
                html.Td("Minimum price reduction allowed")
            ]),
            html.Tr([
                html.Td("Premium Cap %"),
                html.Td(f"{pricing_rules['premium_cap_pct']}%"),
                html.Td("Maximum premium pricing allowed")
            ])
        ])
    ], className="table table-sm")

    return nps_fig, reviews_fig, f"{current_reputation:.1f}", pricing_table


@callback(
    Output("ops-whatif-preview", "children"),
    Input("ops-whatif-slider", "value")
)
def update_whatif_preview(reputation_idx: float):
    """Update what-if pricing preview based on slider value."""

    # Calculate pricing rules based on reputation index
    if reputation_idx >= 80:
        rules = {"max_concession_days": 0, "floor_price_pct": 2.0, "premium_cap_pct": 12.0}
    elif reputation_idx >= 65:
        rules = {"max_concession_days": 7, "floor_price_pct": 5.0, "premium_cap_pct": 8.0}
    elif reputation_idx >= 50:
        rules = {"max_concession_days": 14, "floor_price_pct": 8.0, "premium_cap_pct": 6.0}
    else:
        rules = {"max_concession_days": 21, "floor_price_pct": 12.0, "premium_cap_pct": 4.0}

    preview_table = html.Table([
        html.Thead([
            html.Tr([
                html.Th("Metric"),
                html.Th(f"Value at {reputation_idx:.0f}"),
                html.Th("Description")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td("Max Concession Days"),
                html.Td(f"{rules['max_concession_days']} days", style={"color": "blue"}),
                html.Td("Maximum days of rent concessions")
            ]),
            html.Tr([
                html.Td("Floor Price %"),
                html.Td(f"{rules['floor_price_pct']}%", style={"color": "blue"}),
                html.Td("Minimum price reduction allowed")
            ]),
            html.Tr([
                html.Td("Premium Cap %"),
                html.Td(f"{rules['premium_cap_pct']}%", style={"color": "blue"}),
                html.Td("Maximum premium pricing allowed")
            ])
        ])
    ], className="table table-sm table-bordered")

    return html.Div([
        html.H6("Pricing Preview", className="mb-3"),
        preview_table,
        html.Small("Changes take effect when reputation index reaches this level", className="text-muted")
    ])


@callback(
    Output("ops-upload-results", "children"),
    Output("ops-upload-meta", "data"),
    Input("ops-csv-upload", "contents"),
    State("ops-csv-upload", "filename")
)
def handle_csv_upload(contents: str, filename: str):
    """Handle CSV upload and processing."""

    if not contents:
        return html.Div(), None

    # Parse upload
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        # Process CSV (simplified - would call API in real implementation)
        result = {
            "filename": filename,
            "ingested": 45,
            "rejected": 3,
            "errors": [
                {"row": 12, "error": "Rating outside 1-5 range"},
                {"row": 18, "error": "Invalid date format"}
            ]
        }

        # Create results display
        results_div = html.Div([
            dbc.Alert([
                html.Strong(f"Upload Complete: {result['ingested']} reviews ingested, {result['rejected']} rejected")
            ], color="success", className="mb-3"),

            html.H6("Sample Errors:", className="mt-3"),
            html.Table([
                html.Thead([
                    html.Tr([html.Th("Row"), html.Th("Error")])
                ]),
                html.Tbody([
                    html.Tr([html.Td(error["row"]), html.Td(error["error"])])
                    for error in result["errors"][:5]  # Show first 5 errors
                ])
            ], className="table table-sm table-striped")
        ])

        return results_div, result

    except Exception as e:
        error_div = dbc.Alert([
            html.Strong(f"Upload Failed: {str(e)}")
        ], color="danger")

        return error_div, None


# Layout for the page
layout = create_ops_brand_dashboard
