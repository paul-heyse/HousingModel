"""Unit tests for governance functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from aker_core.governance import (
    ICWorkflow,
    advance,
    get_required_artifacts,
    check_quorum,
    GATE_DEFINITIONS,
    get_gate_sequence,
    validate_gate_transition,
    get_ic_quorum_threshold,
    get_ic_members,
)
from aker_core.governance.config import GateDefinition, ICMember
from aker_core.governance.models import DealGate, GateArtifact, ICApproval, GovernanceAudit


class TestGateDefinitions:
    """Test gate definition configuration."""

    def test_gate_definitions_exist(self):
        """Test that all required gates are defined."""
        expected_gates = ["Screen", "IOI", "LOI", "IC1", "IC2", "Close"]
        assert list(GATE_DEFINITIONS.keys()) == expected_gates

    def test_gate_sequence_order(self):
        """Test that gates are in correct sequence."""
        sequence = get_gate_sequence()
        assert sequence == ["Screen", "IOI", "LOI", "IC1", "IC2", "Close"]

    def test_gate_definition_validation(self):
        """Test gate definition validation."""
        gate_def = GATE_DEFINITIONS["Screen"]
        assert gate_def.name == "Screen"
        assert len(gate_def.required_artifacts) > 0
        assert 0.0 <= gate_def.approval_threshold <= 1.0
        assert gate_def.timeout_hours > 0

    def test_gate_transition_validation(self):
        """Test gate transition validation."""
        # Valid transitions
        assert validate_gate_transition("Screen", "IOI")
        assert validate_gate_transition("IOI", "LOI")
        assert validate_gate_transition("IC1", "IC2")

        # Invalid transitions (skipping)
        assert not validate_gate_transition("Screen", "LOI")
        assert not validate_gate_transition("IOI", "IC2")

        # Invalid backward transitions
        assert not validate_gate_transition("IOI", "Screen")

    def test_get_required_artifacts(self):
        """Test getting required artifacts for gates."""
        screen_artifacts = get_required_artifacts("Screen")
        assert len(screen_artifacts) > 0
        assert "market_analysis_summary" in screen_artifacts

        loi_artifacts = get_required_artifacts("LOI")
        assert "executed_loi_document" in loi_artifacts


class TestICWorkflow:
    """Test IC workflow engine functionality."""

    def test_workflow_initialization(self, db_session):
        """Test workflow initialization."""
        workflow = ICWorkflow(db_session)
        assert workflow.session is db_session

    def test_advance_invalid_gate_transition(self, db_session):
        """Test that invalid gate transitions are rejected."""
        workflow = ICWorkflow(db_session)

        with pytest.raises(ValueError, match="Invalid gate transition"):
            workflow.advance(
                deal_id=1,
                target_gate="LOI",  # Skip IOI
                artifacts=["test.pdf"],
                user_id="test_user"
            )

    def test_advance_missing_artifacts(self, db_session):
        """Test that missing artifacts block advancement."""
        workflow = ICWorkflow(db_session)

        with pytest.raises(ValueError, match="Missing required artifacts"):
            workflow.advance(
                deal_id=1,
                target_gate="IOI",
                artifacts=[],  # No artifacts provided
                user_id="test_user"
            )

    def test_advance_valid_transition(self, db_session):
        """Test valid gate advancement."""
        workflow = ICWorkflow(db_session)

        # First advance to IOI
        deal_gate = workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=["detailed_market_analysis", "property_condition_assessment"],
            user_id="test_user"
        )

        assert deal_gate.deal_id == 1
        assert deal_gate.current_gate == "IOI"

        # Verify artifacts were created
        artifacts = db_session.query(GateArtifact).filter(
            GateArtifact.deal_id == 1,
            GateArtifact.gate == "IOI"
        ).all()

        assert len(artifacts) == 2
        artifact_names = [art.artifact_name for art in artifacts]
        assert "detailed_market_analysis" in artifact_names
        assert "property_condition_assessment" in artifact_names

    def test_approval_submission(self, db_session):
        """Test IC approval submission."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IC1 gate
        deal_gate = workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=["complete_underwriting_package"],
            user_id="test_user"
        )

        # Submit approval
        approval = workflow.submit_approval(
            deal_id=1,
            gate="IC1",
            ic_member="ic_chair",
            approval_type="approve",
            comment="Looks good",
            user_id="test_user"
        )

        assert approval.deal_id == 1
        assert approval.gate == "IC1"
        assert approval.ic_member == "ic_chair"
        assert approval.approval_type == "approve"
        assert approval.comment == "Looks good"

    def test_quorum_checking(self, db_session):
        """Test quorum requirement checking."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IC1 gate
        workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=["complete_underwriting_package"],
            user_id="test_user"
        )

        # Check quorum before approvals
        assert not workflow.check_quorum("IC1", 1)

        # Submit approvals
        workflow.submit_approval(1, "IC1", "ic_chair", "approve")
        workflow.submit_approval(1, "IC1", "ic_member_1", "approve")
        workflow.submit_approval(1, "IC1", "ic_member_2", "approve")

        # Check quorum after approvals
        assert workflow.check_quorum("IC1", 1)

    def test_gate_completion_check(self, db_session):
        """Test gate completion status checking."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IOI gate (no quorum required)
        workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=["detailed_market_analysis", "property_condition_assessment"],
            user_id="test_user"
        )

        # Check completion status
        status = workflow.check_gate_completion(1, "IOI")
        assert status is True

    def test_audit_trail_logging(self, db_session):
        """Test that all actions are logged to audit trail."""
        workflow = ICWorkflow(db_session)

        # Advance deal
        workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=["detailed_market_analysis"],
            user_id="test_user",
            comment="Initial advancement"
        )

        # Check audit entries
        audit_entries = db_session.query(GovernanceAudit).filter(
            GovernanceAudit.deal_id == 1
        ).all()

        assert len(audit_entries) >= 1
        assert any(entry.action == "gate_advance" for entry in audit_entries)


class TestICComposition:
    """Test IC composition and quorum functionality."""

    def test_get_ic_members(self):
        """Test getting active IC members."""
        members = get_ic_members()
        assert len(members) > 0
        assert "ic_chair" in members
        assert "ic_member_1" in members

    def test_ic_member_weights(self):
        """Test that IC members have correct voting weights."""
        members = get_ic_members()

        # Chair should have higher weight
        chair = members["ic_chair"]
        assert chair.voting_weight > 1.0

        # Regular members should have weight 1.0
        member = members["ic_member_1"]
        assert member.voting_weight == 1.0

    def test_quorum_thresholds(self):
        """Test quorum thresholds for different gates."""
        # Screen gate has no quorum requirement
        screen_threshold = get_ic_quorum_threshold("Screen")
        assert screen_threshold == 0.5  # Default for non-quorum gates

        # IC1 gate has higher threshold
        ic1_threshold = get_ic_quorum_threshold("IC1")
        assert ic1_threshold == 0.75

        # Close gate has highest threshold
        close_threshold = get_ic_quorum_threshold("Close")
        assert close_threshold == 0.9


class TestIntegrationScenarios:
    """Test complete governance workflows."""

    def test_complete_deal_lifecycle(self, db_session):
        """Test complete deal progression through all gates."""
        workflow = ICWorkflow(db_session)

        # Screen -> IOI
        deal = workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=["market_analysis_summary", "preliminary_financial_model"],
            user_id="analyst"
        )
        assert deal.current_gate == "IOI"

        # IOI -> LOI
        deal = workflow.advance(
            deal_id=1,
            target_gate="LOI",
            artifacts=["detailed_market_analysis", "property_condition_assessment"],
            user_id="analyst"
        )
        assert deal.current_gate == "LOI"

        # LOI -> IC1
        deal = workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=["executed_loi_document", "detailed_financial_projections"],
            user_id="analyst"
        )
        assert deal.current_gate == "IC1"

        # Submit IC approvals for IC1
        workflow.submit_approval(1, "IC1", "ic_chair", "approve")
        workflow.submit_approval(1, "IC1", "ic_member_1", "approve")
        workflow.submit_approval(1, "IC1", "ic_member_2", "approve")

        # IC1 -> IC2
        deal = workflow.advance(
            deal_id=1,
            target_gate="IC2",
            artifacts=["complete_underwriting_package", "risk_assessment_report"],
            user_id="analyst"
        )
        assert deal.current_gate == "IC2"

        # Final approvals and close
        workflow.submit_approval(1, "IC2", "ic_chair", "approve")
        workflow.submit_approval(1, "IC2", "ic_member_1", "approve")

        deal = workflow.advance(
            deal_id=1,
            target_gate="Close",
            artifacts=["final_investment_memo", "legal_documentation_package"],
            user_id="analyst"
        )
        assert deal.current_gate == "Close"

    def test_gate_skip_prevention(self, db_session):
        """Test that gates cannot be skipped."""
        workflow = ICWorkflow(db_session)

        # Try to skip directly to IC2
        with pytest.raises(ValueError, match="Invalid gate transition"):
            workflow.advance(
                deal_id=1,
                target_gate="IC2",
                artifacts=["test.pdf"],
                user_id="test_user"
            )

    def test_artifact_validation_enforcement(self, db_session):
        """Test that missing artifacts prevent gate advancement."""
        workflow = ICWorkflow(db_session)

        # Try to advance to IOI with missing artifacts
        with pytest.raises(ValueError, match="Missing required artifacts"):
            workflow.advance(
                deal_id=1,
                target_gate="IOI",
                artifacts=["detailed_market_analysis"],  # Missing property_condition_assessment
                user_id="test_user"
            )


class TestConvenienceFunctions:
    """Test convenience functions for governance operations."""

    def test_advance_convenience_function(self, db_session):
        """Test the convenience advance function."""
        # This should work the same as workflow.advance()
        deal = advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=["detailed_market_analysis", "property_condition_assessment"],
            user_id="test_user",
            session=db_session
        )

        assert deal.current_gate == "IOI"

    def test_get_required_artifacts_function(self):
        """Test the convenience function for getting required artifacts."""
        artifacts = get_required_artifacts("LOI")
        assert "executed_loi_document" in artifacts
        assert len(artifacts) > 0

    def test_check_quorum_convenience_function(self, db_session):
        """Test the convenience function for checking quorum."""
        # Set up a deal in IC1
        workflow = ICWorkflow(db_session)
        workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=["complete_underwriting_package"],
            user_id="test_user"
        )

        # No quorum initially
        assert not check_quorum("IC1", 1, db_session)

        # Submit approvals
        workflow.submit_approval(1, "IC1", "ic_chair", "approve")

        # Still no quorum (need more approvals)
        assert not check_quorum("IC1", 1, db_session)


class TestErrorHandling:
    """Test error handling in governance operations."""

    def test_invalid_approval_type(self, db_session):
        """Test handling of invalid approval types."""
        workflow = ICWorkflow(db_session)

        with pytest.raises(ValueError, match="Invalid approval type"):
            workflow.submit_approval(
                deal_id=1,
                gate="IC1",
                ic_member="ic_chair",
                approval_type="invalid_type"
            )

    def test_deal_not_in_gate(self, db_session):
        """Test handling when deal is not in expected gate."""
        workflow = ICWorkflow(db_session)

        with pytest.raises(ValueError, match="Deal .* is not in gate"):
            workflow.submit_approval(
                deal_id=1,
                gate="IC1",  # Deal not in IC1 yet
                ic_member="ic_chair",
                approval_type="approve"
            )

    def test_duplicate_approvals(self, db_session):
        """Test handling of duplicate approval submissions."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IC1
        workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=["complete_underwriting_package"],
            user_id="test_user"
        )

        # Submit first approval
        approval1 = workflow.submit_approval(1, "IC1", "ic_chair", "approve")

        # Submit second approval (should update existing)
        approval2 = workflow.submit_approval(1, "IC1", "ic_chair", "reject")

        # Should be the same record updated
        assert approval1.id == approval2.id
        assert approval2.approval_type == "reject"
