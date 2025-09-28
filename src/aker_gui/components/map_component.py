"""
Interactive map component for Market Scorecard dashboard.

This module provides the interactive map component using dash-leaflet
for displaying MSA boundaries with color-coded pillar scores.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import dash
import dash_leaflet as dl
from dash import dcc, html

from aker_core.config import Settings


def create_map_component(
    msa_data: List[Dict[str, Any]] = None,
    selected_msas: List[str] = None,
    peril_overlays: Dict[str, Dict[str, Any]] = None,
    active_perils: List[str] = None,
    settings: Optional[Settings] = None,
) -> html.Div:
    """
    Create the interactive map component for the Market Scorecard.

    Args:
        msa_data: List of MSA data with scores and boundaries
        selected_msas: Currently selected MSA IDs
        peril_overlays: Dictionary of peril overlay data (GeoJSON)
        active_perils: List of currently active peril types
        settings: Application settings

    Returns:
        Dash HTML component containing the map
    """
    if settings is None:
        # Create a minimal settings object for testing
        class MinimalSettings:
            debug = True
        settings = MinimalSettings()

    if msa_data is None:
        msa_data = []

    if selected_msas is None:
        selected_msas = []

    if peril_overlays is None:
        peril_overlays = {}

    if active_perils is None:
        active_perils = []

    # Create GeoJSON features for MSA boundaries
    geojson_data = create_msa_geojson(msa_data)

    # Create map layers
    layers = [
        # Base map layer
        dl.TileLayer(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        ),
    ]

    # Add peril overlay layers for active perils
    for peril in active_perils:
        if peril in peril_overlays:
            overlay_data = peril_overlays[peril]
            peril_layer = dl.GeoJSON(
                data=overlay_data,
                id=f"{peril}-overlay",
                style=lambda feature: create_peril_style(feature, peril),
                hoverStyle={"weight": 3, "color": "#666", "fillOpacity": 0.8},
                onEachFeature=lambda feature, layer: create_peril_popup_content(feature, layer, peril),
            )
            layers.append(peril_layer)

    # Add MSA boundary layer if we have data
    if geojson_data:
        msa_layer = dl.GeoJSON(
            data=geojson_data,
            id="msa-boundaries",
            style=create_msa_style,
            hoverStyle={"weight": 3, "color": "#666", "fillOpacity": 0.7},
            onEachFeature=create_popup_content,
            cluster=True,
        )
        layers.append(msa_layer)

    # Create the map component
    map_component = html.Div([
        # Map container
        html.Div([
            dl.Map(
                [
                    dl.LayersControl([
                        dl.BaseLayer(
                            dl.TileLayer(
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                            ),
                            name="OpenStreetMap",
                            checked=True,
                        ),
                        dl.Overlay(
                            dl.GeoJSON(
                                data=geojson_data,
                                id="msa-overlay",
                                style=create_msa_style,
                                hoverStyle={"weight": 3, "color": "#666", "fillOpacity": 0.7},
                                onEachFeature=create_popup_content,
                            ),
                            name="MSA Boundaries",
                            checked=True,
                        ),
                    ]),
                ],
                id="market-map",
                center=[39.8283, -98.5795],  # Center of US
                zoom=4,
                style={"height": "500px", "width": "100%"},
            ),
        ], className="map-container mb-3"),

        # Map controls
        html.Div([
            html.H6("Map Controls", className="mb-2"),
            html.Div([
                html.Small("Click on MSA boundaries to view details", className="text-muted"),
            ]),
        ], className="map-controls"),
    ])

    return map_component


def create_msa_geojson(msa_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create GeoJSON data structure for MSA boundaries.

    Args:
        msa_data: List of MSA data with scores and boundaries

    Returns:
        GeoJSON FeatureCollection
    """
    features = []

    for msa in msa_data:
        # Create a simple polygon for demonstration
        # In production, this would come from actual MSA boundary data
        coordinates = create_demo_msa_coordinates(msa.get("msa_id", ""))

        if coordinates:
            feature = {
                "type": "Feature",
                "properties": {
                    "msa_id": msa.get("msa_id", ""),
                    "name": msa.get("name", ""),
                    "state": msa.get("state", ""),
                    "overall_score": msa.get("overall_score", 0),
                    "supply_score": msa.get("supply_score", 0),
                    "jobs_score": msa.get("jobs_score", 0),
                    "urban_score": msa.get("urban_score", 0),
                    "outdoors_score": msa.get("outdoors_score", 0),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coordinates],
                },
            }
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def create_demo_msa_coordinates(msa_id: str) -> List[List[float]]:
    """
    Create demo coordinates for MSA boundaries.

    In production, this would load actual MSA boundary data from GeoJSON files.

    Args:
        msa_id: MSA identifier

    Returns:
        List of coordinate pairs for polygon boundary
    """
    # Demo coordinates for major MSAs
    demo_coordinates = {
        "31080": [  # Los Angeles
            [-118.9448, 33.6989],
            [-117.6462, 33.6989],
            [-117.6462, 34.8231],
            [-118.9448, 34.8231],
            [-118.9448, 33.6989],
        ],
        "19100": [  # Dallas
            [-97.5698, 32.5997],
            [-96.2700, 32.5997],
            [-96.2700, 33.2479],
            [-97.5698, 33.2479],
            [-97.5698, 32.5997],
        ],
        "41860": [  # San Francisco
            [-123.1738, 37.4699],
            [-121.8940, 37.4699],
            [-121.8940, 38.0294],
            [-123.1738, 38.0294],
            [-123.1738, 37.4699],
        ],
    }

    return demo_coordinates.get(msa_id, [])


def create_msa_style(feature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create styling for MSA boundary features based on scores.

    Args:
        feature: GeoJSON feature with MSA properties

    Returns:
        Style dictionary for the feature
    """
    overall_score = feature.get("properties", {}).get("overall_score", 0)

    # Color coding based on overall score (0-5 scale)
    if overall_score >= 4.0:
        color = "#28a745"  # Green for excellent
        fill_opacity = 0.6
    elif overall_score >= 3.0:
        color = "#ffc107"  # Yellow for good
        fill_opacity = 0.5
    elif overall_score >= 2.0:
        color = "#fd7e14"  # Orange for fair
        fill_opacity = 0.4
    else:
        color = "#dc3545"  # Red for poor
        fill_opacity = 0.3

    return {
        "weight": 2,
        "color": color,
        "fillColor": color,
        "fillOpacity": fill_opacity,
    }


def create_popup_content(feature: Dict[str, Any], layer: Any) -> None:
    """
    Create popup content for MSA features.

    Args:
        feature: GeoJSON feature
        layer: Leaflet layer object
    """
    properties = feature.get("properties", {})
    popup_content = f"""
    <div style="width: 200px;">
        <h6>{properties.get("name", "Unknown MSA")}</h6>
        <p><strong>Overall Score:</strong> {properties.get("overall_score", 0):.1f}/5</p>
        <p><strong>MSA ID:</strong> {properties.get("msa_id", "N/A")}</p>
        <p><strong>State:</strong> {properties.get("state", "N/A")}</p>
        <div style="margin-top: 10px;">
            <small>
                <strong>Pillar Scores:</strong><br>
                Supply: {properties.get("supply_score", 0):.1f} |
                Jobs: {properties.get("jobs_score", 0):.1f}<br>
                Urban: {properties.get("urban_score", 0):.1f} |
                Outdoors: {properties.get("outdoors_score", 0):.1f}
            </small>
        </div>
    </div>
    """

    layer.bindPopup(popup_content)


def create_peril_style(feature: Dict[str, Any], peril: str) -> Dict[str, Any]:
    """
    Create styling for peril overlay features based on severity.

    Args:
        feature: GeoJSON feature with peril properties
        peril: Type of peril (wildfire, hail, etc.)

    Returns:
        Style dictionary for the feature
    """
    properties = feature.get("properties", {})
    severity = properties.get("severity", 50)  # Default to medium severity

    # Color coding based on peril type and severity
    if peril == "wildfire":
        color = get_wildfire_color(severity)
    elif peril == "hail":
        color = get_hail_color(severity)
    elif peril == "snow_load":
        color = get_snow_color(severity)
    elif peril == "flood":
        color = get_flood_color(severity)
    elif peril == "water_stress":
        color = get_water_stress_color(severity)
    else:
        color = "#666666"  # Default gray

    return {
        "weight": 2,
        "color": color,
        "fillColor": color,
        "fillOpacity": 0.6,
    }


def create_peril_popup_content(feature: Dict[str, Any], layer: Any, peril: str) -> None:
    """
    Create popup content for peril features.

    Args:
        feature: GeoJSON feature
        layer: Leaflet layer object
        peril: Type of peril
    """
    properties = feature.get("properties", {})

    if peril == "wildfire":
        popup_content = create_wildfire_popup(properties)
    elif peril == "hail":
        popup_content = create_hail_popup(properties)
    elif peril == "snow_load":
        popup_content = create_snow_popup(properties)
    elif peril == "flood":
        popup_content = create_flood_popup(properties)
    elif peril == "water_stress":
        popup_content = create_water_stress_popup(properties)
    else:
        popup_content = f"<div><h6>{peril.title()}</h6><p>Severity: {properties.get('severity', 'Unknown')}</p></div>"

    layer.bindPopup(popup_content)


def get_wildfire_color(severity: float) -> str:
    """Get color for wildfire severity."""
    if severity >= 80:
        return "#d73027"  # Dark red for extreme
    elif severity >= 60:
        return "#f46d43"  # Orange-red for high
    elif severity >= 40:
        return "#fdae61"  # Orange for moderate
    elif severity >= 20:
        return "#fee090"  # Yellow for low
    else:
        return "#e0f3f8"  # Light blue for minimal


def get_hail_color(severity: float) -> str:
    """Get color for hail severity."""
    if severity >= 80:
        return "#542788"  # Purple for extreme
    elif severity >= 60:
        return "#8073ac"  # Light purple for high
    elif severity >= 40:
        return "#b2abd2"  # Very light purple for moderate
    elif severity >= 20:
        return "#d8daeb"  # Very light purple for low
    else:
        return "#f7f7f7"  # Almost white for minimal


def get_snow_color(severity: float) -> str:
    """Get color for snow load severity."""
    if severity >= 80:
        return "#053061"  # Dark blue for extreme
    elif severity >= 60:
        return "#2166ac"  # Medium blue for high
    elif severity >= 40:
        return "#4393c3"  # Light blue for moderate
    elif severity >= 20:
        return "#92c5de"  # Very light blue for low
    else:
        return "#d1e5f0"  # Almost white for minimal


def get_flood_color(severity: float) -> str:
    """Get color for flood severity."""
    if severity >= 80:
        return "#40004b"  # Dark purple for extreme
    elif severity >= 60:
        return "#762a83"  # Medium purple for high
    elif severity >= 40:
        return "#9970ab"  # Light purple for moderate
    elif severity >= 20:
        return "#c2a5cf"  # Very light purple for low
    else:
        return "#e7d4e8"  # Almost white for minimal


def get_water_stress_color(severity: float) -> str:
    """Get color for water stress severity."""
    if severity >= 80:
        return "#b10026"  # Dark red for extreme
    elif severity >= 60:
        return "#e31a1c"  # Red for high
    elif severity >= 40:
        return "#fc4e2a"  # Orange for moderate
    elif severity >= 20:
        return "#fd8d3c"  # Light orange for low
    else:
        return "#fed976"  # Yellow for minimal


def create_wildfire_popup(properties: Dict[str, Any]) -> str:
    """Create popup content for wildfire features."""
    return f"""
    <div style="width: 200px;">
        <h6>Wildfire Risk</h6>
        <p><strong>WUI Class:</strong> {properties.get('wui_class', 'Unknown')}</p>
        <p><strong>Severity Index:</strong> {properties.get('severity', 'N/A')}/100</p>
        <p><strong>Burn Probability:</strong> {properties.get('burn_prob', 'N/A')}%</p>
        <small class="text-muted">Higher values indicate higher wildfire risk</small>
    </div>
    """


def create_hail_popup(properties: Dict[str, Any]) -> str:
    """Create popup content for hail features."""
    return f"""
    <div style="width: 200px;">
        <h6>Hail Risk</h6>
        <p><strong>1-in Hail Frequency:</strong> {properties.get('hail_frequency', 'N/A')}</p>
        <p><strong>Severity Index:</strong> {properties.get('severity', 'N/A')}/100</p>
        <p><strong>Max Hail Size:</strong> {properties.get('max_hail_size', 'N/A')} inches</p>
        <small class="text-muted">Lower frequency numbers indicate higher risk</small>
    </div>
    """


def create_snow_popup(properties: Dict[str, Any]) -> str:
    """Create popup content for snow load features."""
    return f"""
    <div style="width: 200px;">
        <h6>Snow Load Risk</h6>
        <p><strong>Ground Snow Load:</strong> {properties.get('ground_snow_load', 'N/A')} psf</p>
        <p><strong>Severity Index:</strong> {properties.get('severity', 'N/A')}/100</p>
        <p><strong>Design Load:</strong> {properties.get('design_load', 'N/A')} psf</p>
        <small class="text-muted">Higher values indicate higher snow load requirements</small>
    </div>
    """


def create_flood_popup(properties: Dict[str, Any]) -> str:
    """Create popup content for flood features."""
    return f"""
    <div style="width: 200px;">
        <h6>Flood Risk</h6>
        <p><strong>Flood Zone:</strong> {properties.get('flood_zone', 'Unknown')}</p>
        <p><strong>Severity Index:</strong> {properties.get('severity', 'N/A')}/100</p>
        <p><strong>Base Flood Elevation:</strong> {properties.get('bfe', 'N/A')} ft</p>
        <small class="text-muted">Flood zones indicate flood risk level</small>
    </div>
    """


def create_water_stress_popup(properties: Dict[str, Any]) -> str:
    """Create popup content for water stress features."""
    return f"""
    <div style="width: 200px;">
        <h6>Water Stress</h6>
        <p><strong>Water Stress Index:</strong> {properties.get('water_stress_idx', 'N/A')}/100</p>
        <p><strong>Severity:</strong> {properties.get('severity', 'N/A')}/100</p>
        <p><strong>Groundwater Level:</strong> {properties.get('groundwater_level', 'N/A')} ft</p>
        <small class="text-muted">Higher values indicate greater water stress</small>
    </div>
    """


def create_map_controls() -> html.Div:
    """Create map control components."""
    return html.Div([
        html.H6("Map Controls"),
        html.Div([
            html.Button(
                "Reset View",
                id="reset-map-btn",
                className="btn btn-secondary btn-sm me-2",
            ),
            html.Button(
                "Toggle Boundaries",
                id="toggle-boundaries-btn",
                className="btn btn-secondary btn-sm",
            ),
        ]),
    ])


def register_map_callbacks(app: dash.Dash) -> None:
    """Register callbacks for map interactions."""

    @app.callback(
        dash.Output("market-map", "center"),
        dash.Input("reset-map-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_map_view(n_clicks):
        """Reset map to default view."""
        if n_clicks:
            return [39.8283, -98.5795]  # Center of US
        return dash.no_update

    @app.callback(
        dash.Output("msa-overlay", "style"),
        dash.Input("toggle-boundaries-btn", "n_clicks"),
        dash.State("msa-overlay", "style"),
        prevent_initial_call=True,
    )
    def toggle_boundaries(n_clicks, current_style):
        """Toggle MSA boundary visibility."""
        if n_clicks and n_clicks % 2 == 1:  # Odd clicks = hide
            return {"display": "none"}
        else:  # Even clicks or initial = show
            return {"display": "block"}
