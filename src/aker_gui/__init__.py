"""
Aker Property Model GUI - FastAPI + Dash Web Application

Module: aker_gui
Purpose: Provides the main web interface for the Aker Property Model, combining
         FastAPI REST API endpoints with interactive Dash dashboards for
         comprehensive housing investment analysis
Author: Aker Property Model Team
Created: 2025-01-27
Modified: 2025-01-27

Dependencies:
    - fastapi: REST API framework with automatic OpenAPI documentation
    - dash: Interactive web dashboard framework with Plotly integration
    - dash-bootstrap-components: Bootstrap styling for Dash components
    - uvicorn: ASGI server for FastAPI applications
    - gunicorn: WSGI server for production deployment
    - aker_core: Core utilities and configuration management
    - aker_data: Database models and base classes

Configuration:
    - FastAPI application factory with middleware stack
    - CORS, security headers, and request logging
    - Authentication stub with session management
    - Database session management and connection pooling

Environment Variables:
    - AKER_DATABASE_URL: Database connection string
    - AKER_ALLOWED_ORIGINS: CORS allowed origins (comma-separated)
    - AKER_TRUSTED_HOSTS: Trusted host headers (comma-separated)
    - AKER_DEBUG: Enable debug mode (true/false)

API Reference:
    Public Functions:
        create_app(settings=None) -> FastAPI
            Create and configure the main FastAPI application with Dash integration.

        create_dash_app(settings=None) -> Dash
            Create the multi-page Dash application with navigation and routing.

    Public Classes:
        None (application factories only)

    Public Constants:
        None

Examples:
    Basic application setup:

    ```python
    from aker_gui import create_app
    from aker_core.config import Settings

    # Create application with custom settings
    settings = Settings(debug=True, database_url="postgresql://...")
    app = create_app(settings)

    # Run with uvicorn
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    ```

    Production deployment with gunicorn:

    ```bash
    # gunicorn.conf.py
    workers = 4
    bind = "0.0.0.0:8000"
    wsgi_module = "aker_gui.app:create_app()"
    ```

Error Handling:
    - HTTPException: Raised for API errors with appropriate status codes
    - ValidationError: Raised for invalid request data
    - DatabaseError: Raised for database connection issues
    - ConfigurationError: Raised for invalid application configuration

Performance Notes:
    - FastAPI provides automatic request/response serialization
    - Dash applications support real-time updates via WebSocket
    - Database connections are pooled for optimal performance
    - Static file serving optimized for production deployment

Testing:
    Playwright integration tests for end-to-end workflow validation
    Unit tests for API endpoints and dashboard components
    Performance benchmarks for large dataset handling

Security:
    - CORS configuration for cross-origin requests
    - Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
    - Request logging for audit trails
    - Input validation and sanitization
    - Authentication session management

See Also:
    - aker_core.config: Application settings and configuration
    - aker_core.logging: Structured logging and monitoring
    - FastAPI documentation: https://fastapi.tiangolo.com/
    - Dash documentation: https://dash.plotly.com/
"""

from __future__ import annotations

from .app import create_app
from .dash_app import create_dash_app

__all__ = [
    "create_app",
    "create_dash_app",
]
