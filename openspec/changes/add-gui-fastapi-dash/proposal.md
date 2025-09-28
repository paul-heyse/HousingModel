## Why

The Aker Property Model requires a user-friendly GUI for analysts to interact with market scoring, deal analysis, asset evaluation, and portfolio monitoring without writing code. The current system lacks a web interface, forcing users to rely on Python SDK calls and exported reports. A modern web application with FastAPI backend and Dash frontend will provide the interactive experience needed for daily analytical workflows.

## What Changes

- **BREAKING**: New `gui` capability with FastAPI + Dash application
- Add `aker_gui.app:create_app()` application factory
- Implement FastAPI REST API layer at `/api/*` endpoints
- Mount Dash application at `/app` with multi-page layout
- Add authentication stub with session management
- Create 7 core dashboard pages as specified in project.md
- Integrate with all backend modules (markets, assets, deals, portfolio, etc.)
- Add real-time data updates and WebSocket support
- Implement export functionality for Excel/Word/PDF generation
- Add responsive design with mobile support

## Impact

- Affected specs: New `gui` capability spec with comprehensive dashboard requirements
- Affected code: New gui module, integration with all existing modules, database API layer
- Risk: Large new surface area, potential performance impact on existing APIs
- Migration: Existing CLI tools remain functional; new GUI provides alternative interface
- Dependencies: Requires FastAPI, Dash, Uvicorn, Playwright for testing
