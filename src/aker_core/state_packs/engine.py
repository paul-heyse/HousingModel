from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class StateRulePack:
    """State-specific rule pack configuration."""
    state_code: str
    version: str
    defaults: Dict[str, Any]
    perils: Dict[str, float]
    tax_cadence: Dict[str, Any]
    guardrails: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "state_code": self.state_code,
            "version": self.version,
            "defaults": self.defaults,
            "perils": self.perils,
            "tax_cadence": self.tax_cadence,
            "guardrails": self.guardrails,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class StateContext:
    """Context object that gets mutated by state rules."""
    data: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def update(self, other: Dict[str, Any]) -> None:
        self.data.update(other)

    def to_dict(self) -> Dict[str, Any]:
        return self.data.copy()


def _calculate_context_hash(context: Dict[str, Any]) -> str:
    """Calculate a hash of the context for audit trails."""
    # Create a stable representation for hashing
    sorted_items = sorted(context.items())
    context_str = json.dumps(sorted_items, sort_keys=True)
    return hashlib.sha256(context_str.encode()).hexdigest()[:16]


def apply_rules_to_context(rules: StateRulePack, context: StateContext) -> StateContext:
    """Apply state-specific rules to a context object."""

    # Apply defaults
    for key, value in rules.defaults.items():
        if key not in context.data:
            context[key] = value

    # Apply peril multipliers
    for peril_key, multiplier in rules.perils.items():
        if peril_key in context.data:
            context[peril_key] = context[peril_key] * multiplier
        else:
            context[peril_key] = multiplier

    # Apply guardrail adjustments
    for guardrail_key, adjustment in rules.guardrails.items():
        # Map guardrail keys to context keys
        context_key_map = {
            "entitlement_days_buffer": "entitlement_days",
            "water_tap_cost_buffer": "water_tap_cost",
            "topography_slope_buffer": "topography_slope",
            "water_allocation_buffer": "water_allocation",
            "forest_buffer_distance": "forest_buffer_distance",
            "migration_growth_cap": "migration_growth_cap",
            "smoke_season_impact": "smoke_season_impact",
            "design_review_probability": "design_review_probability",
            "winter_construction_penalty": "winter_construction_penalty",
        }

        context_key = context_key_map.get(guardrail_key, guardrail_key)

        if context_key in context.data:
            if isinstance(adjustment, (int, float)) and isinstance(context[context_key], (int, float)):
                # Numeric adjustment (additive for integers, multiplicative for floats)
                if isinstance(adjustment, int):
                    context[context_key] = context[context_key] + adjustment
                elif isinstance(adjustment, float) and adjustment != 1.0:
                    context[context_key] = context[context_key] * adjustment
                else:
                    context[context_key] = adjustment
            else:
                # Direct override
                context[context_key] = adjustment

    # Apply tax cadence rules
    for tax_key, value in rules.tax_cadence.items():
        context[f"tax_{tax_key}"] = value

    return context


def apply(state_code: str, context: Dict[str, Any] | StateContext | None = None) -> StateContext:
    """Apply state-specific rules to a context.

    Args:
        state_code: Two-letter state code (CO, UT, ID)
        context: Context dictionary or StateContext object to mutate

    Returns:
        StateContext with state-specific rules applied

    Raises:
        ValueError: If state_code is invalid or rules cannot be loaded
    """
    if context is None:
        context = StateContext()
    elif isinstance(context, dict):
        context = StateContext(context)
    elif not isinstance(context, StateContext):
        raise ValueError("Context must be dict or StateContext")

    # Validate state code
    valid_states = {"CO", "UT", "ID"}
    if state_code.upper() not in valid_states:
        raise ValueError(f"Invalid state code '{state_code}'. Must be one of: {valid_states}")

    # Load state rules
    try:
        from .config import load_state_rules

        rules = load_state_rules(state_code.upper())
    except Exception as e:
        raise ValueError(f"Failed to load rules for state '{state_code}': {e}")

    # Apply rules to context
    updated_context = apply_rules_to_context(rules, context)

    # Store rule application metadata in context
    updated_context["_state_rules_applied"] = {
        "state_code": state_code.upper(),
        "rule_version": rules.version,
        "applied_at": datetime.now().isoformat(),
        "context_hash": _calculate_context_hash(updated_context.to_dict())
    }

    return updated_context
