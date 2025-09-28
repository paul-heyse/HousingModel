"""
Dash page components for Aker Property Model GUI.

This module contains all the individual dashboard page implementations.
"""

from __future__ import annotations

from .asset_fit_wizard import create_layout as asset_fit_wizard_layout
from .deal_workspace import create_layout as deal_workspace_layout
from .market_scorecard import create_layout as market_scorecard_layout
from .risk_panel import create_layout as risk_panel_layout

__all__ = [
    "market_scorecard_layout",
    "deal_workspace_layout",
    "asset_fit_wizard_layout",
    "risk_panel_layout",
]
