"""
REST API endpoints for Aker Property Model GUI.

This module provides FastAPI routers for all backend functionality.
"""

from __future__ import annotations

from fastapi import APIRouter

from .assets import router as assets_router
from .deals import router as deals_router
from .exports import router as exports_router
from .health import router as health_router
from .markets import router as markets_router
from .portfolio import router as portfolio_router
from .risk import router as risk_router
from .state_packs import router as state_packs_router

# Main API router
router = APIRouter()

# Include sub-routers
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(markets_router, prefix="/markets", tags=["markets"])
router.include_router(assets_router, prefix="/assets", tags=["assets"])
router.include_router(deals_router, prefix="/deals", tags=["deals"])
router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
router.include_router(risk_router, prefix="/risk", tags=["risk"])
router.include_router(exports_router, prefix="/exports", tags=["exports"])
router.include_router(state_packs_router, prefix="/state-packs", tags=["state-packs"])
