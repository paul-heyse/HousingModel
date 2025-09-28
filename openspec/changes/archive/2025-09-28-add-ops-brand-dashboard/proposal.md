## Why
The project specification in project.md section 5 requires "NPS loop → pricing/features; reputation lift reduces concessions & speeds lease" and "Feedback ingestion (reviews/NPS) → Reputation Index → pricing guardrails" as part of the operations model. However, the current system lacks a user-friendly interface for operations teams to monitor reputation metrics, upload review data, and adjust pricing strategies based on reputation performance. Stakeholders need a centralized dashboard to track brand health, manage reputation-driven pricing, and make data-informed operational decisions.

## What Changes
- Implement Ops & Brand dashboard at `/app/ops?asset_id=AKR-123` with comprehensive reputation and pricing management
- Create API endpoints for reputation data retrieval and CSV review upload processing
- Build interactive UI components for NPS/review trend visualization and reputation index display
- Implement pricing guardrail preview system with what-if scenario modeling
- Add CSV upload functionality with validation and error reporting
- Integrate with existing ops engine for reputation index calculation and pricing rules
- Support role-based permissions and telemetry for security and analytics
- Create comprehensive test suite including Playwright integration tests

**BREAKING**: None - this adds new dashboard functionality without modifying existing interfaces

## Impact
- Affected specs: `gui` (new Ops & Brand dashboard requirements), `ops` (enhanced reputation API)
- Affected code: `src/aker_gui/dash_pages/ops_brand_dashboard.py`, `src/aker_gui/api/ops.py`, ops engine extensions
- New dependencies: CSV processing libraries, chart visualization components
- Database impact: Enhanced ops_model table for reputation tracking
- Testing: Playwright end-to-end tests, API contract validation, CSV processing tests
