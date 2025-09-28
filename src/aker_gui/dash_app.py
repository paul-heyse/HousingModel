"""
Dash application for Aker Property Model GUI.

This module creates the multi-page Dash application with navigation,
layout, and all dashboard pages.
"""

from __future__ import annotations

from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html

from aker_core.config import Settings

from .dash_pages import asset_fit_wizard, deal_workspace, market_scorecard, risk_panel


def create_dash_app(settings: Optional[Settings] = None) -> Dash:
    """
    Create and configure the Dash application.

    Args:
        settings: Application settings

    Returns:
        Configured Dash application
    """
    if settings is None:
        settings = Settings()

    # Create Dash app with Bootstrap styling
    app = Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://use.fontawesome.com/releases/v6.0.0/css/all.css",
        ],
        suppress_callback_exceptions=True,
        title="Aker Property Model",
        update_title="Loading...",
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        ],
    )

    # Configure app
    app.config.suppress_callback_exceptions = True

    # Set up navigation
    app.layout = create_layout()

    # Register callbacks
    register_callbacks(app)

    return app


def create_layout() -> html.Div:
    """Create the main application layout."""
    return html.Div([
        # Navigation header
        create_navigation(),

        # Main content area
        html.Div([
            # Page content will be rendered here
            html.Div(id="page-content"),

            # Hidden div for storing user session data
            html.Div(id="user-session-store", style={"display": "none"}),
        ], className="container-fluid"),

        # Footer
        create_footer(),

        # Location component for routing
        dcc.Location(id="url", refresh=False),

        # Store components for state management
        dcc.Store(id="session-store"),
        dcc.Store(id="market-data-store"),
        dcc.Store(id="asset-data-store"),
        dcc.Store(id="portfolio-data-store"),
    ])


def create_navigation() -> dbc.Navbar:
    """Create the navigation header."""
    return dbc.Navbar(
        dbc.Container([
            # Brand/logo
            html.A(
                dbc.Row([
                    dbc.Col(html.I(className="fas fa-home me-2")),
                    dbc.Col(html.Span("Aker Property Model", className="navbar-brand mb-0 h1")),
                ], align="center"),
                href="/app/",
                className="navbar-brand",
            ),

            # Navigation links
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Market Scorecard", href="/app/markets", active="exact")),
                    dbc.NavItem(dbc.NavLink("Deal Workspace", href="/app/deal", active="exact")),
                    dbc.NavItem(dbc.NavLink("Asset Fit Wizard", href="/app/asset-fit", active="exact")),
                    dbc.NavItem(dbc.NavLink("Risk Panel", href="/app/risk", active="exact")),
                    dbc.NavItem(dbc.NavLink("Ops & Brand", href="/app/ops", active="exact")),
                    dbc.NavItem(dbc.NavLink("Data Refresh", href="/app/data", active="exact")),
                    dbc.NavItem(dbc.NavLink("Portfolio", href="/app/portfolio", active="exact")),
                ], className="me-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),

            # User menu (placeholder for authentication)
            dbc.NavbarToggler(id="user-menu-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Login", href="/app/login", active="exact")),
                ], navbar=True),
                id="user-menu-collapse",
                navbar=True,
            ),
        ]),
        color="primary",
        dark=True,
        className="mb-4",
    )


def create_footer() -> dbc.Container:
    """Create the application footer."""
    return dbc.Container([
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.P("© 2025 Aker Property Model", className="mb-0"),
                html.Small("Housing investment analysis platform", className="text-muted"),
            ], md=6),
            dbc.Col([
                html.Small("Version 0.1.0", className="text-muted"),
            ], md=6, className="text-end"),
        ]),
    ], className="mt-4 mb-2")


def register_callbacks(app: Dash) -> None:
    """Register all application callbacks."""

    @app.callback(
        dash.Output("page-content", "children"),
        [dash.Input("url", "pathname")]
    )
    def display_page(pathname):
        """Display the appropriate page based on URL path."""
        if pathname == "/app/" or pathname == "/app":
            return market_scorecard.create_layout()
        elif pathname == "/app/markets":
            return market_scorecard.create_layout()
        elif pathname == "/app/deal":
            return deal_workspace.create_layout()
        elif pathname == "/app/asset-fit":
            return asset_fit_wizard.create_layout()
        elif pathname == "/app/risk":
            return risk_panel.create_layout()
        elif pathname == "/app/ops":
            return html.Div("Ops & Brand - Coming Soon")
        elif pathname == "/app/data":
            return html.Div("Data Refresh - Coming Soon")
        elif pathname == "/app/portfolio":
            return html.Div("Portfolio - Coming Soon")
        elif pathname == "/app/login":
            return html.Div("Login - Coming Soon")
        else:
            return html.Div("404 - Page Not Found")
