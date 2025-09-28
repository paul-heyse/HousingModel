## Why
The project specification in project.md section 22 requires an "IC workflow in app" with "gated artifacts (Screen→IOI→LOI→IC1→IC2→Close)" and "IC composition/quorum". However, the current system lacks a systematic workflow engine for managing investment committee approvals, artifact requirements, and governance processes. Investment committees need structured gate progression with mandatory artifact checklists to ensure proper due diligence and compliance with governance standards.

## What Changes
- Implement IC workflow engine with `ic.advance(deal_id, gate, artifacts=[...])` Python surface
- Create governance capability with state machine for deal progression through gates
- Define artifact checklist system with mandatory requirements per gate
- Implement sign-off and approval workflows with audit trails
- Add database schema for deal state machine and governance audit stamps
- Create governance dashboard for tracking deal progression and bottlenecks
- Integrate with existing risk engine and portfolio management systems
- Support IC composition, quorum requirements, and voting mechanisms

**BREAKING**: None - this adds new governance functionality without modifying existing interfaces

## Impact
- Affected specs: New `governance` capability for IC workflows and decisioning
- Affected code: `src/aker_core/governance/`, database migrations for governance tables
- New dependencies: Workflow engine library (e.g., prefect states or simple state machine)
- Database migrations: New tables for deal states, gate artifacts, approvals, and audit trails
- Testing: Unit tests for workflow progression, integration tests with existing deal management
