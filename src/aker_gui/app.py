"""
FastAPI application factory for Aker Property Model GUI.

This module provides the main application factory that creates a FastAPI app
with both REST API endpoints and Dash web interface.
"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from aker_core.config import Settings
from aker_core.logging import get_logger

from .api import router as api_router
from .dash_app import create_dash_app
from .websocket import create_websocket_endpoint, websocket_manager

logger = get_logger(__name__)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        settings: Application settings (uses default if not provided)

    Returns:
        Configured FastAPI application
    """
    if settings is None:
        # Create a minimal settings object for GUI testing
        # In production, this would use proper database configuration
        class MinimalSettings:
            debug = True
            allowed_origins = ["*"]
            trusted_hosts = None
            database_url = None
            cache_enabled = False
        settings = MinimalSettings()

    # Create FastAPI app
    app = FastAPI(
        title="Aker Property Model",
        description="Housing investment analysis and portfolio management platform",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Add middleware
    _add_middleware(app, settings)

    # Add routes
    _add_routes(app, settings)

    # Add error handlers
    _add_error_handlers(app)

    # Mount static files
    _mount_static_files(app)

    logger.info("FastAPI application created successfully")

    return app


def _add_middleware(app: FastAPI, settings: Settings) -> None:
    """Add middleware to the application."""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if settings.debug:
            response.headers["X-Debug"] = "true"

        return response

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
        )

        return response

    # Trusted hosts middleware (if configured)
    if settings.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts,
        )


def _add_routes(app: FastAPI, settings: Settings) -> None:
    """Add routes to the application."""
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    # Root redirect to Dash app
    @app.get("/")
    async def root():
        """Root endpoint - redirect to Dash app."""
        return {"message": "Aker Property Model API", "docs": "/docs", "app": "/app"}

    # API routes
    app.include_router(api_router, prefix="/api", tags=["api"])

    # WebSocket endpoint for real-time updates
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket, client_id: str):
        """WebSocket endpoint for real-time updates."""
        await websocket_manager.handle_websocket(websocket, client_id)

    # Mount Dash application
    dash_app = create_dash_app(settings)
    app.mount("/app", dash_app.server)


def _add_error_handlers(app: FastAPI) -> None:
    """Add global error handlers."""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        logger.error("unhandled_exception", error=str(exc), url=str(request.url))

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


def _mount_static_files(app: FastAPI) -> None:
    """Mount static files if they exist."""
    # Static files can be added later when we have assets
    pass
