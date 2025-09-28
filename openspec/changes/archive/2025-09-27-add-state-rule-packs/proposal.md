## Why
The project specification in project.md extensively references CO/UT/ID state-specific patterning with distinct operational characteristics, risk profiles, and regulatory environments. However, the current system lacks a systematic way to apply state-specific rule packs that adjust defaults, perils, winterization costs, and tax cadences. Property managers and underwriters need automated state selection that pre-fills appropriate guardrails and risk parameters based on location-specific requirements.

## What Changes
- Implement state rule packs system with `state_packs.apply("CO", context)` Python surface
- Create YAML-based configuration for state-specific defaults, perils, winterization cost adders, and tax cadences
- Add state selector UI component that pre-fills guardrails based on selected state
- Define `state_rules` table schema for persistence and audit trails
- Create state-specific rule engines with emphasis on CO/UT/ID characteristics:
  - **CO**: Aerospace/tech/health anchors, entitlement variance, hail/wildfire insurance patterns
  - **UT**: Tech/higher-ed anchors, topography-driven supply friction, water rights/winter timing
  - **ID**: In-migration patterns, small-scale walkable districts, property tax dynamics, forest-interface wildfire risks
- Integrate with existing risk engine and guardrail systems

**BREAKING**: None - this adds new state-specific functionality without modifying existing interfaces

## Impact
- Affected specs: `core` (state rule pack engine), UI components for state selection
- Affected code: `src/aker_core/state_packs/`, database migrations for `state_rules` table
- New dependencies: YAML parsing library (ruamel.yaml for advanced YAML features)
- Database migrations: New `state_rules` table with snapshots and versioning
- Testing: Unit tests for rule application, integration tests with CO/UT/ID specific scenarios
