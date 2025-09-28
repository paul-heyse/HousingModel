## Context
The Aker property model requires state-specific operational patterns, particularly for Colorado, Utah, and Idaho markets. These states have distinct regulatory environments, risk profiles, and operational characteristics that significantly impact underwriting decisions and operational costs.

## Goals / Non-Goals
- **Goals**:
  - Provide systematic state-specific rule application
  - Enable CO/UT/ID-specific guardrail and risk adjustments
  - Support YAML-based configuration for easy rule updates
  - Integrate with existing risk engine and UI components
- **Non-Goals**:
  - Replace existing risk calculation engines
  - Create state-specific data connectors (use existing ones)
  - Implement real-time state policy monitoring

## Decisions

### State Rule Pack Architecture
- **YAML Configuration**: State rules stored as YAML files for human readability and version control
- **Context Application**: Rules applied to calculation contexts rather than direct database mutation
- **Snapshot Persistence**: Applied rules stored in `state_rules` table for audit trails
- **UI Integration**: State selector component that triggers rule application

### CO/UT/ID Specific Rule Categories
Based on project.md analysis:

**Colorado (CO)**:
- Industry anchors: Aerospace, tech, health sectors
- Regulatory: Entitlement variance, design review requirements
- Perils: Hail exposure, wildfire risk, severe weather patterns
- Operations: Insurance cost adjustments, winterization requirements

**Utah (UT)**:
- Industry anchors: Tech and higher education institutions
- Regulatory: Topography-driven supply constraints, water rights
- Perils: Winter weather timing, geological constraints
- Operations: Water infrastructure costs, seasonal construction timing

**Idaho (ID)**:
- Industry anchors: In-migration patterns, small-scale development
- Regulatory: Property tax dynamics, forest-interface development
- Perils: Wildfire exposure, forest adjacency risks
- Operations: Walkable district development, migration-driven demand

## Implementation Strategy

### Phase 1: Core Engine
```python
# Core interface
def apply(state_code: str, context: Dict) -> Dict:
    """Apply state-specific rules to context."""
    rules = load_state_rules(state_code)
    return apply_rules_to_context(rules, context)
```

### Phase 2: YAML Schema
```yaml
# Example CO rule pack
colorado:
  defaults:
    winterization_cost_multiplier: 1.15
    insurance_base_rate: 0.008
  perils:
    hail_risk_multiplier: 1.25
    wildfire_risk_multiplier: 1.20
  tax_cadence:
    reassessment_frequency: "annual"
    appeal_window_days: 30
  guardrails:
    entitlement_days_buffer: 45
    water_tap_cost_buffer: 0.10
```

### Phase 3: Database Schema
```sql
CREATE TABLE state_rules (
    id SERIAL PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    rule_version VARCHAR(20) NOT NULL,
    rule_snapshot JSONB NOT NULL,
    applied_at TIMESTAMP NOT NULL,
    context_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Risks / Trade-offs

### Performance Impact
- **Risk**: Rule application adds computational overhead
- **Mitigation**: Cache frequently used rule packs, lazy evaluation

### Configuration Complexity
- **Risk**: Complex YAML configurations become hard to maintain
- **Mitigation**: Validation schema, documentation, gradual rollout

### State Policy Changes
- **Risk**: State regulations change requiring rule updates
- **Mitigation**: Versioned rules, audit trails, easy configuration updates

## Migration Plan

1. **Phase 1**: Implement core engine and CO rule pack (Week 1)
2. **Phase 2**: Add UT and ID rule packs (Week 2)
3. **Phase 3**: UI integration and testing (Week 3)
4. **Phase 4**: Database schema and persistence (Week 4)

### Rollback Strategy
- Feature flag controls rule application
- Database snapshots allow rollback to pre-rule state
- YAML configurations can be reverted independently

## Open Questions

- **Rule Precedence**: How should conflicting rules from multiple sources be resolved?
- **Dynamic Updates**: Should rule packs update automatically or require deployment?
- **Testing Strategy**: How to test state-specific rule interactions with existing systems?
- **Documentation**: What level of detail needed for rule configuration documentation?
