## Why

Risk assessment is critical for housing investment underwriting. Analysts need to visualize geographic hazard exposures, model insurance scenarios, and understand how risk factors impact exit cap rates and contingencies. The current system lacks integrated risk visualization and scenario modeling capabilities.

## What Changes

- **BREAKING**: New Risk Panel dashboard with comprehensive hazard analysis
- Add interactive map with peril overlays (WUI, hail, snow load, flood, water stress)
- Implement insurance scenario modeling with deductible and parametric options
- Create risk multiplier visualization and impact analysis
- Add export preview with risk section integration
- Integrate with existing risk engine and geographic data APIs
- Add state management for peril selection and scenario configuration

## Impact

- Affected specs: Enhanced gui capability spec with Risk Panel requirements
- Affected code: New dashboard page, map overlays, scenario engine integration
- Risk: Complex geospatial data integration requires careful performance optimization
- Migration: Replaces placeholder Risk Panel with full implementation
- Dependencies: Requires enhanced geographic APIs, risk engine integration, and vector tile support
