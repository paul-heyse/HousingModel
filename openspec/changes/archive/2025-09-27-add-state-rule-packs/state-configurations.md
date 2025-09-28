# State Rule Pack Configurations (CO/UT/ID)

## Overview
This document details the state-specific rule pack configurations for Colorado, Utah, and Idaho, based on the operational characteristics outlined in project.md. Each state has distinct industry anchors, regulatory environments, peril profiles, and operational requirements.

## Colorado (CO) Rule Pack

### Industry Anchors
- **Aerospace/Tech/Health**: Major employment drivers requiring specialized insurance and development patterns
- **Town-center nodes**: Urban development focus with specific entitlement requirements

### Regulatory Characteristics
- **Entitlement variance**: Higher variability in approval timelines
- **Design review requirements**: Additional regulatory oversight
- **Height/FAR restrictions**: More stringent building code requirements

### Peril Profile
- **Hail exposure**: Significant hail risk requiring specialized insurance
- **Wildfire patterns**: Forest adjacency and wind-driven fire risks
- **Severe weather**: Snow load and freeze/thaw cycle considerations

### Operational Adjustments
```yaml
colorado:
  defaults:
    insurance_base_rate: 0.008  # Higher base due to hail/wildfire
    winterization_cost_multiplier: 1.15
    entitlement_variance_buffer_days: 30

  perils:
    hail_risk_multiplier: 1.25
    wildfire_risk_multiplier: 1.20
    snow_load_factor: 1.18

  tax_cadence:
    reassessment_frequency: "annual"
    appeal_window_days: 30
    mill_levy_volatility: 0.15

  guardrails:
    entitlement_days_buffer: 45
    design_review_probability: 0.85
    water_tap_cost_buffer: 0.08
```

## Utah (UT) Rule Pack

### Industry Anchors
- **Tech/Higher-ed**: University and technology sector concentration
- **Topography constraints**: Mountain terrain limiting development options

### Regulatory Characteristics
- **Water rights**: Complex water allocation systems
- **Topography friction**: Geological constraints on development
- **Winter timing**: Seasonal construction limitations

### Peril Profile
- **Winter weather**: Extended cold periods and snow management
- **Geological risks**: Landslide and seismic considerations
- **Water stress**: Drought and water availability issues

### Operational Adjustments
```yaml
utah:
  defaults:
    water_infrastructure_cost_multiplier: 1.22
    seasonal_construction_discount: 0.12
    topography_constraint_factor: 1.18

  perils:
    winter_weather_risk_multiplier: 1.15
    geological_risk_multiplier: 1.10
    water_stress_factor: 1.08

  tax_cadence:
    reassessment_frequency: "biennial"
    appeal_window_days: 45
    water_rights_assessment: true

  guardrails:
    topography_slope_buffer: 0.15
    water_allocation_buffer: 0.20
    winter_construction_penalty: 0.10
```

## Idaho (ID) Rule Pack

### Industry Anchors
- **In-migration**: Population growth driving demand
- **Small-scale districts**: Walkable development patterns
- **Forest adjacency**: Mixed urban-forest interfaces

### Regulatory Characteristics
- **Property tax dynamics**: Assessment and appeal processes
- **Forest-interface development**: Wildland-urban interface regulations
- **Migration-driven planning**: Growth management requirements

### Peril Profile
- **Wildfire exposure**: Forest adjacency fire risks
- **Forest smoke**: Seasonal air quality impacts
- **Migration volatility**: Population-driven market fluctuations

### Operational Adjustments
```yaml
idaho:
  defaults:
    migration_demand_multiplier: 1.12
    forest_interface_risk_base: 0.15
    walkable_district_bonus: 0.08

  perils:
    wildfire_risk_multiplier: 1.30
    forest_smoke_impact_days: 45
    migration_volatility_factor: 1.10

  tax_cadence:
    reassessment_frequency: "quinquennial"
    appeal_window_days: 60
    growth_adjustment_factor: 1.05

  guardrails:
    forest_buffer_distance: 100  # feet
    migration_growth_cap: 0.15
    smoke_season_impact: 0.12
```

## Implementation Integration

### Context Application
```python
# Example usage in risk calculation
context = {
    "base_insurance_rate": 0.006,
    "entitlement_days": 180,
    "winterization_cost": 5000
}

# Apply Colorado rules
co_context = state_packs.apply("CO", context)
# Results in:
# - base_insurance_rate: 0.0075 (0.006 * 1.25)
# - entitlement_days: 225 (180 + 45 buffer)
# - winterization_cost: 5750 (5000 * 1.15)
```

### UI Integration
- State selector dropdown with CO/UT/ID options
- Automatic guardrail pre-filling based on selection
- Visual indicators for state-specific adjustments
- Tooltips explaining state-specific rule applications

### Validation Framework
- **Guardrail Mutation Tests**: Verify correct parameter adjustments
- **Risk Cost Validation**: Ensure peril multipliers apply correctly
- **Integration Tests**: Test with realistic market scenarios
- **Performance Benchmarks**: Rule application timing validation

## Data Sources Integration

### Required External Data
- **Property Tax Records**: State-specific assessment patterns
- **Insurance Industry Data**: Hail/wildfire claim frequencies by state
- **Weather/Climate Data**: Seasonal patterns and extreme weather events
- **Regulatory Databases**: Entitlement and permitting timelines

### Integration Points
- **Census/ACS**: Population migration and demographic data
- **FEMA NFHL**: Flood zone and natural hazard data
- **State Revenue Departments**: Tax assessment and appeal processes
- **Insurance Bureau Data**: Premium and claim pattern analysis

## Monitoring and Maintenance

### Rule Versioning
- Semantic versioning for rule pack updates
- Database snapshots for audit trails
- Rollback capabilities for rule configuration errors

### Performance Monitoring
- Rule application timing metrics
- Cache hit rates for frequently used configurations
- Memory usage patterns for large context applications

### Configuration Updates
- YAML validation on deployment
- Automated testing for rule pack changes
- Documentation updates for new state characteristics

This implementation provides a robust foundation for state-specific operational modeling while maintaining flexibility for future regulatory and market changes in the CO/UT/ID region.
