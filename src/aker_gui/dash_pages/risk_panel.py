"""
Risk Panel dashboard page for Aker Property Model GUI.

This page provides comprehensive risk assessment with hazard visualization,
insurance scenario modeling, and risk multiplier analysis.
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from ..components.data_vintage_banner import create_data_vintage_banner
from ..components.map_component import create_map_component
from ..components.risk_export_preview import create_export_preview, register_export_preview_callbacks
from ..components.risk_multipliers_table import create_risk_multipliers_table, create_impact_summary_cards, register_table_callbacks


def create_layout() -> html.Div:
    """Create the Risk Panel page layout."""
    return html.Div([
        # Page header
        html.H1("Risk & Resilience Panel", className="mb-4"),
        html.P("Comprehensive hazard analysis and insurance scenario modeling", className="text-muted"),

        # Data vintage banner
        create_data_vintage_banner(),

        # Controls and configuration
        dbc.Row([
            # Scope and ID selectors
            dbc.Col([
                html.Label("Analysis Scope:"),
                dcc.Dropdown(
                    id="risk-scope-selector",
                    options=[
                        {"label": "Market Analysis", "value": "market"},
                        {"label": "Asset Analysis", "value": "asset"},
                    ],
                    value="market",
                    placeholder="Select analysis scope...",
                ),
            ], md=3),

            dbc.Col([
                html.Label("Target:"),
                dcc.Dropdown(
                    id="risk-target-selector",
                    placeholder="Select MSA or Asset...",
                    disabled=True,  # Will be enabled based on scope
                ),
            ], md=4),

            dbc.Col([
                html.Label("Actions:"),
                dbc.ButtonGroup([
                    dbc.Button("Refresh Data", id="risk-refresh-btn", color="primary"),
                    dbc.Button("Export Analysis", id="risk-export-btn", color="secondary"),
                ]),
            ], md=5),
        ], className="mb-4"),

        # Main content area
        dbc.Row([
            # Left sidebar - Peril selection and scenario configuration
            dbc.Col([
                create_peril_sidebar(),
            ], md=4),

            # Main content - Map and analysis
            dbc.Col([
                dbc.Tabs([
                    dbc.Tab([
                        # Interactive map with peril overlays
                        create_map_section(),
                    ], label="Geographic Risk"),

                    dbc.Tab([
                        # Multipliers table and impact analysis
                        create_analysis_section(),
                    ], label="Risk Analysis"),

                    dbc.Tab([
                        # Export preview
                        create_export_preview(),
                    ], label="Export Preview"),
                ]),
            ], md=8),
        ]),

        # Hidden components for state management
        dcc.Store(id="risk-data-store"),
        dcc.Store(id="selected-perils-store"),
        dcc.Store(id="scenario-config-store"),
        dcc.Store(id="map-layers-store"),
    ])


def create_peril_sidebar() -> html.Div:
    """Create the left sidebar with peril selection and scenario configuration."""
    return html.Div([
        html.H5("Hazard Analysis", className="mb-3"),

        # Peril selection checklist
        html.H6("Select Hazards to Analyze:"),
        dcc.Checklist(
            id="peril-checklist",
            options=[
                {"label": "Wildfire WUI", "value": "wildfire"},
                {"label": "Hail Zones", "value": "hail"},
                {"label": "Snow Load", "value": "snow_load"},
                {"label": "Flood Risk", "value": "flood"},
                {"label": "Water Stress", "value": "water_stress"},
            ],
            value=["wildfire"],  # Default selection
            className="mb-4",
        ),

        # Scenario configuration
        html.H6("Insurance Scenario:", className="mb-3"),
        html.Div([
            # Deductible configurations
            html.H6("Deductibles:", className="mb-2"),
            html.Div([
                html.Small("Wildfire: ", className="text-muted"),
                dcc.Dropdown(
                    id="wildfire-deductible",
                    options=[
                        {"label": "$10,000", "value": "10000"},
                        {"label": "$25,000", "value": "25000"},
                        {"label": "$50,000", "value": "50000"},
                        {"label": "$100,000", "value": "100000"},
                        {"label": "$250,000", "value": "250000"},
                    ],
                    value="50000",
                    className="mb-2",
                ),
            ]),

            html.Div([
                html.Small("Hail: ", className="text-muted"),
                dcc.Dropdown(
                    id="hail-deductible",
                    options=[
                        {"label": "$5,000", "value": "5000"},
                        {"label": "$10,000", "value": "10000"},
                        {"label": "$25,000", "value": "25000"},
                        {"label": "$50,000", "value": "50000"},
                    ],
                    value="10000",
                    className="mb-2",
                ),
            ]),

            # Parametric options
            html.H6("Parametric Coverage:", className="mb-2"),
            dcc.Checklist(
                id="parametric-options",
                options=[
                    {"label": "Wind Speed Triggers", "value": "wind_speed"},
                    {"label": "Precipitation Thresholds", "value": "precipitation"},
                    {"label": "Temperature Extremes", "value": "temperature"},
                ],
                value=[],
                className="mb-3",
            ),

            # Apply scenario button
            dbc.Button(
                "Apply Scenario",
                id="apply-scenario-btn",
                color="primary",
                className="w-100",
            ),
        ]),

        # Scenario summary
        html.Div(id="scenario-summary", className="mt-3 p-2 bg-light rounded"),
    ], className="border-end pe-3")


def create_map_section() -> html.Div:
    """Create the map section with peril overlays."""
    return html.Div([
        html.H5("Geographic Hazard Analysis"),
        html.P("Interactive map showing hazard exposures and risk concentrations", className="text-muted mb-3"),

        # Map component with peril overlays - will be updated via callback
        html.Div(id="map-container"),

        # Map controls
        html.Div([
            html.H6("Map Layers", className="mb-2"),
            dcc.Checklist(
                id="map-layer-toggles",
                options=[
                    {"label": "Wildfire WUI", "value": "wildfire"},
                    {"label": "Hail Zones", "value": "hail"},
                    {"label": "Snow Load", "value": "snow_load"},
                    {"label": "Flood Risk", "value": "flood"},
                    {"label": "Water Stress", "value": "water_stress"},
                ],
                value=["wildfire"],
                className="mb-3",
            ),
        ], className="mt-3"),
    ])


def create_analysis_section() -> html.Div:
    """Create the risk analysis section with multipliers table and impact summary."""
    return html.Div([
        html.H5("Risk Multiplier Analysis"),
        html.P("Impact of selected perils on exit cap rates and contingencies", className="text-muted mb-3"),

        # Multipliers table
        create_risk_multipliers_table(),

        # Impact summary cards
        create_impact_summary_cards(),
    ])


def create_export_preview_section() -> html.Div:
    """Create the export preview section."""
    return html.Div([
        html.H5("Export Preview"),
        html.P("Preview how risk analysis will appear in generated reports", className="text-muted mb-3"),

        # Preview frame
        html.Div([
            html.Iframe(
                id="risk-export-preview",
                src="/api/exports/risk-preview",  # Will be implemented
                width="100%",
                height="600px",
                style={"border": "1px solid #ddd", "border-radius": "4px"},
            ),
        ]),

        # Preview controls
        html.Div([
            html.H6("Preview Controls", className="mt-3"),
            dbc.ButtonGroup([
                dbc.Button("Refresh Preview", id="refresh-preview-btn", color="primary", size="sm"),
                dbc.Button("Download PDF", id="download-preview-btn", color="secondary", size="sm"),
            ]),
        ]),
    ])


def register_callbacks(app: dash.Dash) -> None:
    """Register callbacks for the Risk Panel page."""

    @app.callback(
        dash.Output("risk-target-selector", "disabled"),
        dash.Output("risk-target-selector", "options"),
        dash.Input("risk-scope-selector", "value"),
    )
    def update_target_selector(scope):
        """Update target selector based on scope selection."""
        if scope == "market":
            return False, [
                {"label": "Boise, ID (MSA: 14260)", "value": "14260"},
                {"label": "Salt Lake City, UT (MSA: 41620)", "value": "41620"},
                {"label": "Denver, CO (MSA: 19740)", "value": "19740"},
            ]
        elif scope == "asset":
            return False, [
                {"label": "AKR-001 - Downtown Boise", "value": "AKR-001"},
                {"label": "AKR-002 - Salt Lake Suburb", "value": "AKR-002"},
            ]
        else:
            return True, []

    @app.callback(
        dash.Output("scenario-summary", "children"),
        [dash.Input("wildfire-deductible", "value"),
         dash.Input("hail-deductible", "value"),
         dash.Input("parametric-options", "value")],
    )
    def update_scenario_summary(wildfire_ded, hail_ded, parametrics):
        """Update scenario summary based on configuration."""
        summary = [
            html.P(f"Wildfire Deductible: ${wildfire_ded or 'N/A'}", className="mb-1"),
            html.P(f"Hail Deductible: ${hail_ded or 'N/A'}", className="mb-1"),
        ]

        if parametrics:
            summary.append(html.P(f"Parametrics: {', '.join(parametrics)}", className="mb-1"))

        summary.append(html.Small("Click 'Apply Scenario' to calculate impacts", className="text-muted"))

        return summary

    @app.callback(
        dash.Output("multipliers-table-container", "children"),
        dash.Input("apply-scenario-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def update_multipliers_table(n_clicks):
        """Update multipliers table when scenario is applied."""
        # This would normally fetch real data from the API
        # For now, return placeholder
        return html.Div([
            html.P("Multipliers table will be populated with scenario data", className="text-muted"),
            html.Small("Integration with risk engine pending", className="text-muted"),
        ])

    # Register peril toggling callbacks
    @app.callback(
        dash.Output("risk-data-store", "data"),
        [dash.Input("peril-checklist", "value")],
        prevent_initial_call=True,
    )
    def update_selected_perils(selected_perils):
        """Update selected perils in store."""
        return {"selected_perils": selected_perils or []}

    @app.callback(
        dash.Output("map-container", "children"),
        [dash.Input("risk-data-store", "data")],
        prevent_initial_call=True,
    )
    def update_map_perils(risk_data):
        """Update map with selected perils."""
        selected_perils = risk_data.get("selected_perils", []) if risk_data else []

        # This would normally fetch real peril overlay data from API
        # For now, return the map component
        return create_map_component(active_perils=selected_perils)

    @app.callback(
        dash.Output("multipliers-table-container", "children"),
        dash.Input("apply-scenario-btn", "n_clicks"),
        dash.State("risk-data-store", "data"),
        prevent_initial_call=True,
    )
    def update_multipliers_on_scenario(n_clicks, risk_data):
        """Update multipliers table when scenario is applied."""
        # This would normally fetch real data from the API
        selected_perils = risk_data.get("selected_perils", []) if risk_data else []

        from ..components.risk_multipliers_table import create_risk_multipliers_table
        return create_risk_multipliers_table()

    # Register table callbacks
    register_table_callbacks(app)

    # Register export preview callbacks
    register_export_preview_callbacks(app)
