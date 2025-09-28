## Why

The Market Scorecard is the primary interface for viewing and analyzing market performance data. Users need an interactive map interface with pillar score visualization, data vintage tracking, and export capabilities to effectively evaluate markets for investment decisions.

## What Changes

- **BREAKING**: New interactive Market Scorecard dashboard page
- Add `dash-leaflet` map component with MSA boundaries and score visualization
- Implement pillar score cards with real-time data binding
- Create data vintage banner with refresh indicators
- Add export functionality for Excel/Word/PDF generation
- Integrate with existing market scoring and data APIs
- Add MSA selection and filtering capabilities

## Impact

- Affected specs: Enhanced gui capability spec with Market Scorecard requirements
- Affected code: New dashboard page, map components, data binding
- Risk: UI complexity requires careful performance optimization
- Migration: Replaces placeholder Market Scorecard with full implementation
- Dependencies: Requires dash-leaflet, mapbox integration, and enhanced API layer
