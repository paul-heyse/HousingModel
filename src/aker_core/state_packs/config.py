from __future__ import annotations

from functools import lru_cache
from typing import Dict

from .engine import StateRulePack


class ColoradoRules(StateRulePack):
    """Colorado-specific rule pack."""

    def __init__(self):
        super().__init__(
            state_code="CO",
            version="1.0.0",
            defaults={
                "insurance_base_rate": 0.008,  # Higher base due to hail/wildfire
                "winterization_cost_multiplier": 1.15,
                "entitlement_variance_buffer_days": 30,
            },
            perils={
                "hail_risk_multiplier": 1.25,
                "wildfire_risk_multiplier": 1.20,
                "snow_load_factor": 1.18,
            },
            tax_cadence={
                "reassessment_frequency": "annual",
                "appeal_window_days": 30,
                "mill_levy_volatility": 0.15,
            },
            guardrails={
                "entitlement_days_buffer": 45,
                "design_review_probability": 0.85,
                "water_tap_cost_buffer": 0.08,
            }
        )


class UtahRules(StateRulePack):
    """Utah-specific rule pack."""

    def __init__(self):
        super().__init__(
            state_code="UT",
            version="1.0.0",
            defaults={
                "water_infrastructure_cost_multiplier": 1.22,
                "seasonal_construction_discount": 0.12,
                "topography_constraint_factor": 1.18,
            },
            perils={
                "winter_weather_risk_multiplier": 1.15,
                "geological_risk_multiplier": 1.10,
                "water_stress_factor": 1.08,
            },
            tax_cadence={
                "reassessment_frequency": "biennial",
                "appeal_window_days": 45,
                "water_rights_assessment": True,
            },
            guardrails={
                "topography_slope_buffer": 0.15,
                "water_allocation_buffer": 0.20,
                "winter_construction_penalty": 0.10,
            }
        )


class IdahoRules(StateRulePack):
    """Idaho-specific rule pack."""

    def __init__(self):
        super().__init__(
            state_code="ID",
            version="1.0.0",
            defaults={
                "migration_demand_multiplier": 1.12,
                "forest_interface_risk_base": 0.15,
                "walkable_district_bonus": 0.08,
            },
            perils={
                "wildfire_risk_multiplier": 1.30,
                "forest_smoke_impact_days": 45,
                "migration_volatility_factor": 1.10,
            },
            tax_cadence={
                "reassessment_frequency": "quinquennial",
                "appeal_window_days": 60,
                "growth_adjustment_factor": 1.05,
            },
            guardrails={
                "forest_buffer_distance": 100,  # feet
                "migration_growth_cap": 0.15,
                "smoke_season_impact": 0.12,
            }
        )


@lru_cache(maxsize=3)
def load_state_rules(state_code: str) -> StateRulePack:
    """Load state-specific rules with caching.

    Args:
        state_code: Two-letter state code (CO, UT, ID)

    Returns:
        StateRulePack for the specified state

    Raises:
        ValueError: If state_code is not supported
    """
    rules_map = {
        "CO": ColoradoRules,
        "UT": UtahRules,
        "ID": IdahoRules,
    }

    if state_code not in rules_map:
        raise ValueError(f"Unsupported state code: {state_code}")

    return rules_map[state_code]()


def get_available_states() -> Dict[str, str]:
    """Get mapping of state codes to descriptions."""
    return {
        "CO": "Colorado - Aerospace/tech/health anchors, hail/wildfire patterns",
        "UT": "Utah - Tech/higher-ed anchors, topography constraints, water rights",
        "ID": "Idaho - In-migration patterns, forest wildfire risks, walkable districts",
    }


def validate_state_rule_pack(rules: StateRulePack) -> bool:
    """Validate a state rule pack for completeness and correctness.

    Args:
        rules: StateRulePack to validate

    Returns:
        True if valid, raises ValueError if invalid
    """
    if not rules.state_code:
        raise ValueError("State code cannot be empty")

    if not rules.version:
        raise ValueError("Version cannot be empty")

    # Validate required peril multipliers are present and reasonable
    required_perils = ["hail_risk_multiplier", "wildfire_risk_multiplier"]
    for peril in required_perils:
        if peril not in rules.perils:
            raise ValueError(f"Required peril '{peril}' missing from {rules.state_code} rules")
        if not 0.5 <= rules.perils[peril] <= 3.0:
            raise ValueError(f"Peril multiplier '{peril}' for {rules.state_code} is outside reasonable range (0.5-3.0)")

    # Validate tax cadence has required fields
    required_tax_fields = ["reassessment_frequency", "appeal_window_days"]
    for field in required_tax_fields:
        if field not in rules.tax_cadence:
            raise ValueError(f"Required tax field '{field}' missing from {rules.state_code} rules")

    return True
