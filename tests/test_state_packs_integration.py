"""Integration tests for state rule packs with database and real scenarios."""

from datetime import datetime

from aker_core.database import StatePacksRepository
from aker_core.state_packs import StateContext, apply


class TestStatePacksDatabaseIntegration:
    """Integration tests for state rule packs with database persistence."""

    def test_database_persistence_integration(self, db_session):
        """Test that rule applications are properly persisted."""
        repo = StatePacksRepository(db_session)

        # Apply Colorado rules
        context = {
            "insurance_rate": 0.006,
            "entitlement_days": 180,
            "winterization_cost": 5000
        }

        result = apply("CO", context)
        context_hash = result["_state_rules_applied"]["context_hash"]

        # Save to database
        rule_record = repo.save_rule_application(
            state_code="CO",
            rule_version="1.0.0",
            rule_snapshot=result.to_dict(),
            context_hash=context_hash
        )

        # Verify database record
        assert rule_record.state_code == "CO"
        assert rule_record.rule_version == "1.0.0"
        assert rule_record.context_hash == context_hash
        assert isinstance(rule_record.applied_at, datetime)

    def test_rule_history_retrieval(self, db_session):
        """Test retrieving rule application history."""
        repo = StatePacksRepository(db_session)

        # Apply rules for multiple states
        contexts = [
            ("CO", {"insurance_rate": 0.006}),
            ("UT", {"water_cost": 1000}),
            ("ID", {"migration_factor": 1.0}),
        ]

        records = []
        for state_code, context in contexts:
            result = apply(state_code, context)
            record = repo.save_rule_application(
                state_code=state_code,
                rule_version="1.0.0",
                rule_snapshot=result.to_dict(),
                context_hash=result["_state_rules_applied"]["context_hash"]
            )
            records.append((state_code, record))

        # Test retrieving all history
        all_history = repo.get_rule_history()
        assert len(all_history) >= 3

        # Test filtering by state
        co_history = repo.get_rule_history(state_code="CO")
        assert len(co_history) >= 1
        assert all(record.state_code == "CO" for record in co_history)

        # Test context change detection
        for state_code, record in records:
            context_changes = repo.get_context_changes(record.context_hash)
            assert len(context_changes) >= 1
            assert all(change.context_hash == record.context_hash for change in context_changes)


class TestRealWorldScenarios:
    """Test state rule packs with realistic market scenarios."""

    def test_colorado_aerospace_market_scenario(self):
        """Test Colorado rules for aerospace/tech market."""
        # Simulate Denver/Boulder aerospace corridor
        context = {
            "insurance_rate": 0.005,  # Base rate
            "entitlement_days": 150,  # Typical for CO
            "winterization_cost": 8000,  # Higher due to weather
            "tech_employment_ratio": 0.25,  # High tech concentration
            "hail_risk": 1.0,
            "wildfire_risk": 1.0
        }

        result = apply("CO", context)

        # Verify Colorado-specific adjustments
        assert result["hail_risk_multiplier"] == 1.25
        assert result["wildfire_risk_multiplier"] == 1.20
        assert result["tax_reassessment_frequency"] == "annual"
        assert result["tax_appeal_window_days"] == 30

        # Verify guardrail adjustments
        assert result["entitlement_days"] == 195  # 150 + 45 buffer
        assert result["winterization_cost"] == 9200  # 8000 * 1.15

    def test_utah_university_market_scenario(self):
        """Test Utah rules for university-adjacent market."""
        # Simulate Provo/Salt Lake university corridor
        context = {
            "water_infrastructure_cost": 1500,  # Higher due to water rights
            "topography_constraint": 1.2,  # Mountain terrain
            "seasonal_construction_factor": 1.0,
            "winter_weather_risk": 1.0,
            "geological_risk": 1.0
        }

        result = apply("UT", context)

        # Verify Utah-specific adjustments
        assert result["winter_weather_risk_multiplier"] == 1.15
        assert result["water_infrastructure_cost_multiplier"] == 1.22
        assert result["water_infrastructure_cost"] == 1830  # 1500 * 1.22
        assert result["topography_constraint"] == 1.38  # 1.2 * 1.15 (multiplicative)
        assert result["tax_reassessment_frequency"] == "biennial"
        assert result["tax_water_rights_assessment"]

    def test_idaho_migration_market_scenario(self):
        """Test Idaho rules for high-migration growth market."""
        # Simulate Boise/Twin Falls migration corridor
        context = {
            "migration_demand": 1.0,
            "forest_interface_risk": 0.8,  # Forest adjacency
            "walkable_district_factor": 1.0,
            "wildfire_risk": 1.0,
            "forest_smoke_risk": 1.0
        }

        result = apply("ID", context)

        # Verify Idaho-specific adjustments
        assert result["wildfire_risk_multiplier"] == 1.30
        assert result["migration_demand_multiplier"] == 1.12
        assert result["migration_demand"] == 1.12  # 1.0 * 1.12
        assert result["forest_interface_risk"] == 1.04  # 0.8 * 1.30
        assert result["forest_buffer_distance"] == 100
        assert result["tax_reassessment_frequency"] == "quinquennial"

    def test_portfolio_level_state_application(self):
        """Test applying state rules to portfolio-level analysis."""
        # Multi-state portfolio context
        portfolio_context = {
            "colorado_properties": 25,
            "utah_properties": 15,
            "idaho_properties": 10,
            "total_insurance_cost": 50000,
            "average_entitlement_days": 165,
            "total_winterization_cost": 75000
        }

        # Apply rules for different states to different contexts
        co_context = StateContext(portfolio_context.copy())
        ut_context = StateContext(portfolio_context.copy())
        id_context = StateContext(portfolio_context.copy())

        co_result = apply("CO", co_context)
        ut_result = apply("UT", ut_context)
        id_result = apply("ID", id_context)

        # Verify state-specific adjustments
        assert co_result["hail_risk_multiplier"] == 1.25
        assert ut_result["water_infrastructure_cost_multiplier"] == 1.22
        assert id_result["migration_demand_multiplier"] == 1.12

        # Verify each maintains separate audit trails
        assert co_result["_state_rules_applied"]["state_code"] == "CO"
        assert ut_result["_state_rules_applied"]["state_code"] == "UT"
        assert id_result["_state_rules_applied"]["state_code"] == "ID"

        # Verify different context hashes due to different rule applications
        assert co_result["_state_rules_applied"]["context_hash"] != ut_result["_state_rules_applied"]["context_hash"]
        assert ut_result["_state_rules_applied"]["context_hash"] != id_result["_state_rules_applied"]["context_hash"]
