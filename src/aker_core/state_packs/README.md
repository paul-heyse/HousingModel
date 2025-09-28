# State Rule Packs Module

The `aker_core.state_packs` module provides state-specific rule application for Colorado, Utah, and Idaho markets. This module applies location-based defaults, perils, winterization cost adders, and tax cadences based on the operational characteristics outlined in the project specification.

## Quick Start

```python
from aker_core.state_packs import apply

# Apply Colorado-specific rules
context = {
    "insurance_rate": 0.006,
    "entitlement_days": 180,
    "winterization_cost": 5000
}

result = apply("CO", context)

# Colorado-specific adjustments applied:
# - hail_risk_multiplier: 1.25
# - wildfire_risk_multiplier: 1.20
# - entitlement_days: 225 (180 + 45 buffer)
# - winterization_cost: 5750 (5000 * 1.15)
# - tax_reassessment_frequency: "annual"
```

## API Reference

### `apply(state_code, context) -> StateContext`

Apply state-specific rules to a context object.

**Parameters:**
- `state_code` (str): Two-letter state code ("CO", "UT", "ID")
- `context` (dict | StateContext): Context to apply rules to

**Returns:** `StateContext` with state-specific rules applied

**Raises:**
- `ValueError`: If state_code is invalid or rules cannot be loaded

### `StateContext` Class

Context object that gets mutated by state rules.

**Methods:**
- `__getitem__(key)`: Get value by key
- `__setitem__(key, value)`: Set value by key
- `__contains__(key)`: Check if key exists
- `get(key, default=None)`: Get value with default
- `update(other)`: Update with another dictionary
- `to_dict()`: Convert to dictionary

### `StateRulePack` Class

State-specific rule pack configuration.

**Attributes:**
- `state_code` (str): Two-letter state code
- `version` (str): Rule pack version
- `defaults` (dict): Default values to apply
- `perils` (dict): Risk multipliers by peril type
- `tax_cadence` (dict): Tax-related configurations
- `guardrails` (dict): Guardrail adjustments

## State-Specific Rule Configurations

### Colorado (CO)
**Industry Anchors**: Aerospace, tech, health sectors
**Regulatory**: Entitlement variance, design review requirements
**Perils**: Hail exposure, wildfire risk, severe weather patterns
**Operations**: Insurance cost adjustments, winterization requirements

### Utah (UT)
**Industry Anchors**: Tech and higher education institutions
**Regulatory**: Topography-driven supply constraints, water rights
**Perils**: Winter weather timing, geological constraints
**Operations**: Water infrastructure costs, seasonal construction timing

### Idaho (ID)
**Industry Anchors**: In-migration patterns, small-scale development
**Regulatory**: Property tax dynamics, forest-interface development
**Perils**: Wildfire exposure, forest adjacency risks
**Operations**: Walkable district development, migration-driven demand

## Usage Examples

### Basic State Rule Application
```python
from aker_core.state_packs import apply

# Colorado market analysis
co_context = {
    "base_insurance_rate": 0.006,
    "entitlement_days": 180,
    "winterization_cost": 5000
}

co_result = apply("CO", co_context)
print(f"CO insurance rate: {co_result['hail_risk_multiplier'] * co_result['wildfire_risk_multiplier'] * 0.006:.4f}")
print(f"CO entitlement days: {co_result['entitlement_days']}")
```

### Multi-State Portfolio Analysis
```python
from aker_core.state_packs import apply

portfolio = {
    "colorado_assets": 25,
    "utah_assets": 15,
    "idaho_assets": 10,
    "total_insurance_cost": 50000
}

# Apply state-specific adjustments
co_portfolio = apply("CO", portfolio.copy())
ut_portfolio = apply("UT", portfolio.copy())
id_portfolio = apply("ID", portfolio.copy())

# Each portfolio now has state-specific adjustments
print(f"CO insurance multiplier: {co_portfolio['hail_risk_multiplier']}")
print(f"UT water cost multiplier: {ut_portfolio['water_infrastructure_cost_multiplier']}")
print(f"ID migration multiplier: {id_portfolio['migration_demand_multiplier']}")
```

### Database Integration
```python
from aker_core.state_packs import apply
from aker_core.database import StatePacksRepository

# Apply rules and save to database
context = {"insurance_rate": 0.006, "entitlement_days": 180}
result = apply("CO", context)

# Persist for audit trail
with Session(engine) as session:
    repo = StatePacksRepository(session)
    repo.save_rule_application(
        state_code="CO",
        rule_version="1.0.0",
        rule_snapshot=result.to_dict(),
        context_hash=result["_state_rules_applied"]["context_hash"]
    )
```

### Integration with Risk Engine
```python
from aker_core.state_packs import apply
from aker_core.risk import calculate_risk_premium

# Apply state rules before risk calculation
market_context = {
    "base_premium": 0.02,
    "hail_risk": 1.0,
    "wildfire_risk": 1.0,
    "entitlement_days": 180
}

# Apply Colorado-specific adjustments
co_context = apply("CO", market_context)

# Calculate risk with state-adjusted values
risk_premium = calculate_risk_premium(co_context)
print(f"Colorado-adjusted risk premium: {risk_premium:.4f}")
```

## Rule Configuration

### YAML Schema
State rule packs are defined in YAML format for easy maintenance:

```yaml
colorado:
  defaults:
    insurance_base_rate: 0.008
    winterization_cost_multiplier: 1.15
  perils:
    hail_risk_multiplier: 1.25
    wildfire_risk_multiplier: 1.20
  tax_cadence:
    reassessment_frequency: "annual"
    appeal_window_days: 30
  guardrails:
    entitlement_days_buffer: 45
    water_tap_cost_buffer: 0.08
```

### Rule Categories

**Defaults**: Base values applied when not present in context
**Perils**: Risk multipliers applied to existing peril values
**Tax Cadence**: Tax-related configurations and timing
**Guardrails**: Operational parameter adjustments (additive/multiplicative)

## Testing

Run the test suite:

```bash
# Unit tests
python -m pytest tests/test_state_packs.py -v

# Integration tests
python -m pytest tests/test_state_packs_integration.py -v
```

## Performance Benchmarks

- **Rule Loading**: < 1ms per state (cached)
- **Rule Application**: < 1ms per context
- **Memory Usage**: Minimal (rule packs cached in memory)
- **Database Operations**: < 10ms for audit trail persistence

## Validation

All state rule packs are validated for:
- Required peril multipliers (hail, wildfire)
- Reasonable multiplier ranges (0.5-3.0)
- Required tax cadence fields
- State code and version presence

This implementation provides a robust foundation for state-specific operational modeling while maintaining flexibility for future regulatory and market changes in the CO/UT/ID region.
