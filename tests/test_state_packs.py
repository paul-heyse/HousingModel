"""Unit tests for state rule packs functionality."""

from datetime import datetime

import pytest

from aker_core.state_packs import (
    ColoradoRules,
    IdahoRules,
    StateContext,
    StateRulePack,
    UtahRules,
    apply,
    get_available_states,
    load_state_rules,
    validate_state_rule_pack,
)


class TestStateContext:
    """Test StateContext functionality."""

    def test_state_context_creation(self):
        """Test StateContext can be created empty or with data."""
        # Empty context
        ctx1 = StateContext()
        assert len(ctx1.data) == 0

        # Context with initial data
        initial_data = {"key1": "value1", "key2": 42}
        ctx2 = StateContext(initial_data)
        assert ctx2.data == initial_data
        assert ctx2["key1"] == "value1"
        assert ctx2["key2"] == 42

    def test_state_context_mutation(self):
        """Test StateContext can be mutated."""
        ctx = StateContext({"initial": "value"})

        # Test __setitem__
        ctx["new_key"] = "new_value"
        assert ctx["new_key"] == "new_value"

        # Test __contains__
        assert "new_key" in ctx
        assert "missing_key" not in ctx

        # Test get with default
        assert ctx.get("existing", "default") == "new_value"
        assert ctx.get("missing", "default") == "default"

        # Test update
        ctx.update({"another": "value", "new_key": "updated"})
        assert ctx["another"] == "value"
        assert ctx["new_key"] == "updated"


class TestStateRulePack:
    """Test StateRulePack functionality."""

    def test_state_rule_pack_creation(self):
        """Test StateRulePack can be created with all required fields."""
        rules = StateRulePack(
            state_code="CO",
            version="1.0.0",
            defaults={"test": "value"},
            perils={"hail": 1.25},
            tax_cadence={"frequency": "annual"},
            guardrails={"buffer": 30}
        )

        assert rules.state_code == "CO"
        assert rules.version == "1.0.0"
        assert rules.defaults == {"test": "value"}
        assert rules.perils == {"hail": 1.25}
        assert rules.tax_cadence == {"frequency": "annual"}
        assert rules.guardrails == {"buffer": 30}
        assert isinstance(rules.created_at, datetime)

    def test_state_rule_pack_to_dict(self):
        """Test StateRulePack serialization."""
        rules = StateRulePack(
            state_code="UT",
            version="2.0.0",
            defaults={"test": "value"},
            perils={"snow": 1.15},
            tax_cadence={"frequency": "biennial"},
            guardrails={"buffer": 45}
        )

        data = rules.to_dict()
        assert data["state_code"] == "UT"
        assert data["version"] == "2.0.0"
        assert data["defaults"] == {"test": "value"}
        assert data["perils"] == {"snow": 1.15}
        assert data["tax_cadence"] == {"frequency": "biennial"}
        assert data["guardrails"] == {"buffer": 45}
        assert "created_at" in data


class TestStateRuleApplication:
    """Test state rule application functionality."""

    def test_apply_invalid_state_code(self):
        """Test that invalid state codes raise ValueError."""
        with pytest.raises(ValueError, match="Invalid state code"):
            apply("XX", {})

    def test_apply_empty_context(self):
        """Test applying rules to empty context."""
        context = apply("CO", {})
        assert "_state_rules_applied" in context
        assert context["_state_rules_applied"]["state_code"] == "CO"

    def test_apply_with_initial_context(self):
        """Test applying rules to context with initial data."""
        initial_context = {
            "insurance_rate": 0.006,
            "entitlement_days": 180
        }

        context = apply("CO", initial_context)

        # Should have applied Colorado rules
        assert "_state_rules_applied" in context
        assert context["_state_rules_applied"]["state_code"] == "CO"

        # Should preserve original data
        assert context["insurance_rate"] == 0.006
        assert context["entitlement_days"] == 180

    def test_colorado_rule_application(self):
        """Test Colorado-specific rule application."""
        context = StateContext({
            "insurance_rate": 0.006,
            "entitlement_days": 180,
            "winterization_cost": 5000
        })

        result = apply("CO", context)

        # Check that Colorado-specific adjustments were applied
        assert result["hail_risk_multiplier"] == 1.25  # From Colorado rules
        assert result["wildfire_risk_multiplier"] == 1.20
        assert result["tax_reassessment_frequency"] == "annual"
        assert result["tax_appeal_window_days"] == 30

        # Check guardrail adjustments
        assert result["entitlement_days"] == 225  # 180 + 45 buffer
        assert result["winterization_cost"] == 5750  # 5000 * 1.15

    def test_utah_rule_application(self):
        """Test Utah-specific rule application."""
        context = StateContext({
            "water_cost": 1000,
            "topography_factor": 1.0
        })

        result = apply("UT", context)

        # Check Utah-specific adjustments
        assert result["winter_weather_risk_multiplier"] == 1.15
        assert result["water_infrastructure_cost_multiplier"] == 1.22
        assert result["tax_reassessment_frequency"] == "biennial"
        assert result["tax_water_rights_assessment"]

    def test_idaho_rule_application(self):
        """Test Idaho-specific rule application."""
        context = StateContext({
            "migration_factor": 1.0,
            "forest_buffer": 0
        })

        result = apply("ID", context)

        # Check Idaho-specific adjustments
        assert result["wildfire_risk_multiplier"] == 1.30
        assert result["migration_demand_multiplier"] == 1.12
        assert result["tax_reassessment_frequency"] == "quinquennial"
        assert result["forest_buffer_distance"] == 100

    def test_context_hash_generation(self):
        """Test that context hashes are generated consistently."""
        context1 = StateContext({"a": 1, "b": 2})
        context2 = StateContext({"b": 2, "a": 1})  # Same content, different order

        result1 = apply("CO", context1)
        result2 = apply("CO", context2)

        # Should generate same hash for same content
        assert result1["_state_rules_applied"]["context_hash"] == result2["_state_rules_applied"]["context_hash"]

    def test_multiple_applications(self):
        """Test applying rules multiple times to same context."""
        context = StateContext({"value": 100})

        # Apply Colorado rules
        context = apply("CO", context)
        co_hash = context["_state_rules_applied"]["context_hash"]

        # Apply again (should be idempotent)
        context = apply("CO", context)
        assert context["_state_rules_applied"]["context_hash"] == co_hash

        # Apply different state
        context = apply("UT", context)
        assert context["_state_rules_applied"]["state_code"] == "UT"
        assert context["_state_rules_applied"]["context_hash"] != co_hash


class TestStateRuleValidation:
    """Test state rule pack validation."""

    def test_validate_valid_rule_pack(self):
        """Test validation of valid rule pack."""
        rules = ColoradoRules()
        assert validate_state_rule_pack(rules)

    def test_validate_missing_state_code(self):
        """Test validation fails with missing state code."""
        rules = StateRulePack(
            state_code="",
            version="1.0.0",
            defaults={},
            perils={"hail": 1.25},
            tax_cadence={"frequency": "annual"},
            guardrails={}
        )

        with pytest.raises(ValueError, match="State code cannot be empty"):
            validate_state_rule_pack(rules)

    def test_validate_missing_version(self):
        """Test validation fails with missing version."""
        rules = StateRulePack(
            state_code="CO",
            version="",
            defaults={},
            perils={"hail": 1.25},
            tax_cadence={"frequency": "annual"},
            guardrails={}
        )

        with pytest.raises(ValueError, match="Version cannot be empty"):
            validate_state_rule_pack(rules)

    def test_validate_missing_required_perils(self):
        """Test validation fails with missing required perils."""
        rules = StateRulePack(
            state_code="CO",
            version="1.0.0",
            defaults={},
            perils={"other": 1.0},  # Missing hail and wildfire multipliers
            tax_cadence={"frequency": "annual"},
            guardrails={}
        )

        with pytest.raises(ValueError, match="Required peril 'hail_risk_multiplier' missing"):
            validate_state_rule_pack(rules)

    def test_validate_invalid_peril_multiplier(self):
        """Test validation fails with invalid peril multiplier range."""
        rules = StateRulePack(
            state_code="CO",
            version="1.0.0",
            defaults={},
            perils={"hail_risk_multiplier": 5.0},  # Too high
            tax_cadence={"frequency": "annual"},
            guardrails={}
        )

        with pytest.raises(ValueError, match="outside reasonable range"):
            validate_state_rule_pack(rules)

    def test_validate_missing_tax_fields(self):
        """Test validation fails with missing required tax fields."""
        rules = StateRulePack(
            state_code="CO",
            version="1.0.0",
            defaults={},
            perils={"hail_risk_multiplier": 1.25, "wildfire_risk_multiplier": 1.20},
            tax_cadence={"other": "field"},  # Missing required fields
            guardrails={}
        )

        with pytest.raises(ValueError, match="Required tax field 'reassessment_frequency' missing"):
            validate_state_rule_pack(rules)


class TestStateRuleLoading:
    """Test state rule loading functionality."""

    def test_load_colorado_rules(self):
        """Test loading Colorado rules."""
        rules = load_state_rules("CO")
        assert isinstance(rules, ColoradoRules)
        assert rules.state_code == "CO"
        assert rules.version == "1.0.0"

    def test_load_utah_rules(self):
        """Test loading Utah rules."""
        rules = load_state_rules("UT")
        assert isinstance(rules, UtahRules)
        assert rules.state_code == "UT"

    def test_load_idaho_rules(self):
        """Test loading Idaho rules."""
        rules = load_state_rules("ID")
        assert isinstance(rules, IdahoRules)
        assert rules.state_code == "ID"

    def test_load_invalid_state(self):
        """Test loading invalid state raises error."""
        with pytest.raises(ValueError, match="Unsupported state code"):
            load_state_rules("XX")

    def test_get_available_states(self):
        """Test getting available states mapping."""
        states = get_available_states()
        assert "CO" in states
        assert "UT" in states
        assert "ID" in states
        assert len(states) == 3

        # Check descriptions contain expected content
        assert "Colorado" in states["CO"]
        assert "Utah" in states["UT"]
        assert "Idaho" in states["ID"]


class TestIntegration:
    """Integration tests for state rule packs."""

    def test_end_to_end_colorado_workflow(self):
        """Test complete Colorado workflow."""
        # Initial context
        context = {
            "insurance_rate": 0.006,
            "entitlement_days": 180,
            "winterization_cost": 5000,
            "hail_risk": 1.0,
            "wildfire_risk": 1.0
        }

        # Apply Colorado rules
        result = apply("CO", context)

        # Verify all Colorado-specific adjustments
        assert result["hail_risk_multiplier"] == 1.25
        assert result["wildfire_risk_multiplier"] == 1.20
        assert result["tax_reassessment_frequency"] == "annual"
        assert result["tax_appeal_window_days"] == 30
        assert result["entitlement_days"] == 225  # 180 + 45
        assert result["winterization_cost"] == 5750  # 5000 * 1.15

        # Verify audit trail
        audit = result["_state_rules_applied"]
        assert audit["state_code"] == "CO"
        assert "context_hash" in audit

    def test_rule_application_idempotent(self):
        """Test that applying same rules multiple times is idempotent."""
        context = {"value": 100}

        result1 = apply("CO", context)
        result2 = apply("CO", result1.to_dict())

        # Should produce same results
        assert result1.to_dict() == result2.to_dict()
