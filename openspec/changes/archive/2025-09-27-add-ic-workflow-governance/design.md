## Context
The Aker property model requires a robust governance system for investment committee decision-making. Section 22 of project.md specifies "IC workflow in app" with "gated artifacts (Screen→IOI→LOI→IC1→IC2→Close)" and "IC composition/quorum". The current system lacks structured workflow management for deal progression through mandatory approval gates.

## Goals / Non-Goals
- **Goals**:
  - Implement systematic IC workflow with enforced gate progression
  - Provide artifact checklist validation and sign-off mechanisms
  - Support IC composition, quorum, and voting workflows
  - Maintain complete audit trails for governance compliance
  - Create governance dashboard for deal progression monitoring
- **Non-Goals**:
  - Replace existing deal management systems
  - Implement real-time collaboration features
  - Create document management system (use existing artifact storage)

## Decisions

### Workflow State Machine Architecture
- **State Machine Pattern**: Deal progression as finite state machine with enforced transitions
- **Gate Sequence**: Screen → IOI → LOI → IC1 → IC2 → Close (no skipping allowed)
- **Artifact Requirements**: Each gate has mandatory artifact checklist
- **Approval Workflows**: Multi-step approval process with quorum requirements

### IC Governance Structure
Based on project.md section 22:
- **IC Composition**: Configurable committee membership and roles
- **Quorum Requirements**: Minimum participation thresholds for valid decisions
- **Gated Artifacts**: Mandatory documents/checklists per approval stage
- **Risk/ESG Committees**: Separate approval tracks for specialized oversight

### Database Schema Design
```sql
-- Deal state machine
CREATE TABLE deal_gates (
    deal_id INT PRIMARY KEY,
    current_gate VARCHAR(20) NOT NULL,
    entered_at TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    FOREIGN KEY (deal_id) REFERENCES assets(asset_id)
);

-- Gate artifacts and requirements
CREATE TABLE gate_artifacts (
    id SERIAL PRIMARY KEY,
    deal_id INT NOT NULL,
    gate VARCHAR(20) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL,
    artifact_name VARCHAR(200) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT true,
    provided BOOLEAN NOT NULL DEFAULT false,
    provided_at TIMESTAMP,
    provided_by VARCHAR(100),
    FOREIGN KEY (deal_id) REFERENCES deal_gates(deal_id)
);

-- IC approvals and voting
CREATE TABLE ic_approvals (
    id SERIAL PRIMARY KEY,
    deal_id INT NOT NULL,
    gate VARCHAR(20) NOT NULL,
    ic_member VARCHAR(100) NOT NULL,
    approval_type VARCHAR(20) NOT NULL, -- 'approve', 'reject', 'abstain'
    comment TEXT,
    approved_at TIMESTAMP NOT NULL,
    FOREIGN KEY (deal_id) REFERENCES deal_gates(deal_id)
);

-- Governance audit trail
CREATE TABLE governance_audit (
    id SERIAL PRIMARY KEY,
    deal_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    gate VARCHAR(20),
    user_id VARCHAR(100) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (deal_id) REFERENCES deal_gates(deal_id)
);
```

## Implementation Strategy

### Phase 1: Core Workflow Engine
```python
# Core workflow interface
class ICWorkflow:
    def advance(self, deal_id: int, target_gate: str, artifacts: List[str]) -> DealState:
        """Advance deal to next gate with artifact validation."""

    def get_required_artifacts(self, gate: str) -> List[str]:
        """Get required artifacts for a specific gate."""

    def check_quorum(self, gate: str, deal_id: int) -> bool:
        """Verify IC quorum requirements are met."""
```

### Phase 2: State Machine Implementation
- **Valid Transitions**: Enforce Screen→IOI→LOI→IC1→IC2→Close sequence
- **Artifact Validation**: Checklist verification before gate advancement
- **Rollback Prevention**: No backward movement except for corrections
- **Timeout Handling**: Automatic escalation for stalled approvals

### Phase 3: Approval Workflows
- **IC Composition**: Configurable committee membership and roles
- **Voting Mechanisms**: Support for approve/reject/abstain votes
- **Quorum Tracking**: Real-time quorum status monitoring
- **Approval Thresholds**: Configurable approval percentages per gate

### Phase 4: Audit and Reporting
- **Complete Audit Trail**: Every action logged with user and timestamp
- **Artifact Provenance**: Track document versions and approval history
- **Compliance Reporting**: Generate governance compliance reports
- **Dashboard Integration**: Real-time deal progression monitoring

## Gate Definitions and Artifacts

### Screen Gate
**Purpose**: Initial deal screening and basic validation
**Artifacts Required**:
- Market analysis summary
- Preliminary financial model
- Asset overview document
- Risk assessment checklist

### IOI Gate (Indication of Interest)
**Purpose**: Formal expression of interest with initial due diligence
**Artifacts Required**:
- Detailed market analysis
- Property condition assessment
- Initial underwriting model
- Environmental screening report

### LOI Gate (Letter of Intent)
**Purpose**: Binding commitment with detailed terms
**Artifacts Required**:
- Executed LOI document
- Detailed financial projections
- Legal due diligence summary
- Insurance requirements analysis

### IC1 Gate (Investment Committee Round 1)
**Purpose**: Initial IC review and preliminary approval
**Artifacts Required**:
- Complete underwriting package
- Risk assessment report
- ESG compliance checklist
- Portfolio impact analysis

### IC2 Gate (Investment Committee Round 2)
**Purpose**: Final IC review and funding approval
**Artifacts Required**:
- Final investment memo
- Legal documentation package
- Insurance and risk transfer analysis
- Exit strategy documentation

### Close Gate
**Purpose**: Transaction completion and documentation
**Artifacts Required**:
- Closing documentation
- Final funding confirmation
- Post-close compliance checklist
- Performance tracking setup

## Integration Points

### Existing System Integration
- **Deal Management**: Hook into existing deal lifecycle
- **Portfolio Management**: Update exposure tracking on approvals
- **Risk Engine**: Incorporate governance decisions into risk calculations
- **Reporting**: Include governance metrics in standard reports

### User Interface Integration
- **Gate Status Dashboard**: Visual workflow progression
- **Artifact Upload Interface**: Document management per gate
- **Approval Interface**: Voting and sign-off mechanisms
- **Bottleneck Alerts**: Notification system for stalled deals

## Risks / Trade-offs

### Workflow Complexity
- **Risk**: Complex state machine becomes difficult to maintain
- **Mitigation**: Clear gate definitions, comprehensive testing, gradual rollout

### Performance Impact
- **Risk**: Workflow validation adds latency to deal progression
- **Mitigation**: Async processing, caching of validation results, performance monitoring

### User Experience
- **Risk**: Strict artifact requirements create friction in workflow
- **Mitigation**: Clear UI guidance, bulk upload capabilities, helpful error messages

### Compliance Requirements
- **Risk**: Audit trail requirements become overly burdensome
- **Mitigation**: Automated audit generation, configurable retention policies

## Migration Plan

1. **Phase 1**: Core workflow engine and state machine (Week 1-2)
2. **Phase 2**: Artifact validation and approval workflows (Week 3-4)
3. **Phase 3**: IC composition and voting mechanisms (Week 5-6)
4. **Phase 4**: Dashboard integration and reporting (Week 7-8)

### Rollback Strategy
- Feature flags control workflow enforcement
- Database snapshots allow rollback to pre-governance state
- Gradual rollout by deal type and complexity

## Open Questions

- **Gate Customization**: Should gates be configurable per deal type or organization?
- **Approval Delegation**: How to handle IC member unavailability during approval windows?
- **Emergency Procedures**: How to handle urgent deals requiring expedited approval?
- **Integration Complexity**: How to balance governance rigor with operational efficiency?
