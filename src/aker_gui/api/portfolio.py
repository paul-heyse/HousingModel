"""
Portfolio API endpoints for the GUI application.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_portfolio():
    """List portfolio positions."""
    return {"portfolio": [], "message": "Portfolio API - Coming Soon"}
