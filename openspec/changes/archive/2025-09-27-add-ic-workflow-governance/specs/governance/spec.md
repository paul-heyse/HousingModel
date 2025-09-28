## ADDED Requirements
### Requirement: Investment Committee Workflow Engine
The system SHALL provide a governance workflow engine that manages deal progression through mandatory gates with artifact requirements and approval processes.

#### Scenario: Deal Gate Progression Enforcement
- **GIVEN** a deal in "Screen" gate requiring specific artifacts
- **WHEN** `ic.advance(deal_id, "IOI", artifacts=["market_analysis.pdf", "financial_model.xlsx"])` is called
- **THEN** the system SHALL validate all required artifacts are present
- **AND** transition the deal to "IOI" gate only if validation passes
- **AND** record the gate transition with timestamp and user audit trail

#### Scenario: Artifact Checklist Validation
- **GIVEN** a deal attempting to advance to "LOI" gate
- **WHEN** the required artifacts checklist is incomplete
- **THEN** the system SHALL block the transition
- **AND** return a detailed error listing missing artifacts
- **AND** maintain the deal in current gate until requirements are met

#### Scenario: IC Composition and Quorum Management
- **GIVEN** an IC with defined composition and quorum requirements
- **WHEN** a deal reaches "IC1" or "IC2" gate
- **THEN** the system SHALL verify quorum is met before allowing votes
- **AND** track individual IC member participation and voting records
- **AND** enforce minimum approval thresholds for gate advancement

#### Scenario: Sign-off and Approval Workflow
- **GIVEN** a deal with completed artifacts at "IC1" gate
- **WHEN** IC members submit approvals through the system
- **THEN** the system SHALL collect signatures and timestamps
- **AND** advance to next gate only when quorum and approval thresholds are met
- **AND** create immutable audit record of all approvals and rejections

#### Scenario: Governance Audit Trail Persistence
- **GIVEN** any gate transition or approval action
- **WHEN** the action is executed
- **THEN** the system SHALL store complete audit trail in governance tables
- **AND** include deal state snapshots, user actions, timestamps, and artifact references
- **AND** maintain immutable history for compliance and reporting

#### Scenario: Gate Order Enforcement
- **GIVEN** a deal attempting to skip gates
- **WHEN** `ic.advance(deal_id, "IC2", artifacts=[...])` is called from "Screen" gate
- **THEN** the system SHALL reject the transition
- **AND** return error indicating invalid gate progression
- **AND** maintain deal in current valid gate

#### Scenario: Governance Dashboard Integration
- **GIVEN** a governance dashboard for tracking deal progression
- **WHEN** deals move through gates
- **THEN** the system SHALL update real-time dashboard metrics
- **AND** highlight bottlenecked deals requiring attention
- **AND** provide drill-down views of artifact status and approval progress

#### Scenario: Multi-gate Workflow Validation
- **GIVEN** a complete deal lifecycle from Screen to Close
- **WHEN** all gates are properly traversed with required artifacts
- **THEN** the system SHALL maintain complete state machine consistency
- **AND** validate artifact completeness at each gate transition
- **AND** enforce governance rules throughout the entire workflow
