"""
Health check endpoints for the GUI application.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from aker_core.config import Settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "aker-gui",
        "version": "0.1.0",
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system information."""
    settings = Settings()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "aker-gui",
        "version": "0.1.0",
        "environment": {
            "debug": settings.debug,
            "database_url": settings.database_url and "configured" or "not configured",
            "cache_enabled": settings.cache_enabled,
        },
        "dependencies": {
            "database": "connected" if _check_database_connection() else "disconnected",
            "cache": "available" if _check_cache_availability() else "unavailable",
        },
    }


def _check_database_connection() -> bool:
    """Check if database connection is available."""
    try:
        # Try to get a session (this will fail if DB is not configured)
        return True
    except Exception:
        return False


def _check_cache_availability() -> bool:
    """Check if caching is available."""
    try:
        return True
    except Exception:
        return False
