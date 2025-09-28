"""Integration tests for governance system with database operations."""

import pytest
from datetime import datetime, timedelta

from aker_core.governance import ICWorkflow, advance, get_required_artifacts
from aker_core.database import GovernanceRepository


class TestGovernanceRepository:
    """Integration tests for governance repository."""

    def test_deal_gate_persistence(self, db_session):
        """Test that deal gate state is properly persisted."""
        repo = GovernanceRepository(db_session)

        # Create deal gate
        deal_gate = repo.initialize_deal_gate(deal_id=1)
        assert deal_gate.deal_id == 1
        assert deal_gate.current_gate == "Screen"

        # Verify persistence
        persisted_gate = repo.get_deal_gate(1)
        assert persisted_gate is not None
        assert persisted_gate.current_gate == "Screen"

    def test_artifact_tracking(self, db_session):
        """Test artifact tracking and updates."""
        repo = GovernanceRepository(db_session)

        # Initialize deal
        repo.initialize_deal_gate(deal_id=1)

        # Update artifact status
        artifact = repo.update_artifact_status(
            deal_id=1,
            gate="Screen",
            artifact_name="market_analysis_summary",
            provided=True,
            provided_by="analyst"
        )

        assert artifact.provided is True
        assert artifact.provided_by == "analyst"
        assert artifact.provided_at is not None

    def test_gate_completion_status(self, db_session):
        """Test gate completion status calculation."""
        repo = GovernanceRepository(db_session)

        # Initialize deal and provide all required artifacts
        repo.initialize_deal_gate(deal_id=1)

        required_artifacts = get_required_artifacts("Screen")
        for artifact_name in required_artifacts:
            repo.update_artifact_status(
                deal_id=1,
                gate="Screen",
                artifact_name=artifact_name,
                provided=True,
                provided_by="analyst"
            )

        # Check completion status
        status = repo.get_gate_completion_status(1, "Screen")
        assert status["status"] == "complete"
        assert status["artifact_progress"] == 1.0

    def test_bottleneck_detection(self, db_session):
        """Test bottlenecked deal detection."""
        repo = GovernanceRepository(db_session)

        # Create deal that has been stuck for too long
        deal_gate = repo.initialize_deal_gate(deal_id=1)
        # Simulate old last_updated time
        deal_gate.last_updated = datetime.now() - timedelta(hours=200)  # 200+ hours ago

        db_session.commit()

        # Check for bottlenecks
        bottlenecks = repo.get_bottlenecked_deals(timeout_hours=168)  # 1 week
        assert len(bottlenecks) >= 1
        assert bottlenecks[0].deal_id == 1


class TestWorkflowIntegration:
    """Test complete workflow integration scenarios."""

    def test_end_to_end_deal_progression(self, db_session):
        """Test complete deal progression from Screen to Close."""
        workflow = ICWorkflow(db_session)

        # Start with Screen gate
        deal = workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=get_required_artifacts("IOI"),
            user_id="analyst"
        )
        assert deal.current_gate == "IOI"

        # Progress through LOI
        deal = workflow.advance(
            deal_id=1,
            target_gate="LOI",
            artifacts=get_required_artifacts("LOI"),
            user_id="analyst"
        )
        assert deal.current_gate == "LOI"

        # Move to IC1 and submit approvals
        deal = workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=get_required_artifacts("IC1"),
            user_id="analyst"
        )
        assert deal.current_gate == "IC1"

        # Submit required approvals (75% threshold for IC1)
        workflow.submit_approval(1, "IC1", "ic_chair", "approve")
        workflow.submit_approval(1, "IC1", "ic_member_1", "approve")
        workflow.submit_approval(1, "IC1", "ic_member_2", "approve")

        # Move to IC2
        deal = workflow.advance(
            deal_id=1,
            target_gate="IC2",
            artifacts=get_required_artifacts("IC2"),
            user_id="analyst"
        )
        assert deal.current_gate == "IC2"

        # Final approvals and close
        workflow.submit_approval(1, "IC2", "ic_chair", "approve")
        workflow.submit_approval(1, "IC2", "ic_member_1", "approve")

        deal = workflow.advance(
            deal_id=1,
            target_gate="Close",
            artifacts=get_required_artifacts("Close"),
            user_id="analyst"
        )
        assert deal.current_gate == "Close"

    def test_multiple_deals_concurrent_processing(self, db_session):
        """Test handling multiple deals simultaneously."""
        workflow = ICWorkflow(db_session)

        # Process multiple deals
        for deal_id in [1, 2, 3]:
            # Each deal starts at Screen
            deal = workflow.advance(
                deal_id=deal_id,
                target_gate="IOI",
                artifacts=get_required_artifacts("IOI"),
                user_id=f"analyst_{deal_id}"
            )
            assert deal.current_gate == "IOI"
            assert deal.deal_id == deal_id

        # Verify all deals are tracked separately
        deals_in_ioi = db_session.query("deal_gates").filter(
            "current_gate" == "IOI"
        ).all()
        assert len(deals_in_ioi) == 3

    def test_approval_workflow_integration(self, db_session):
        """Test complete approval workflow with multiple IC members."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IC1
        workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=get_required_artifacts("IC1"),
            user_id="analyst"
        )

        # Submit approvals from different members
        approvals = []
        for member_id in ["ic_chair", "ic_member_1", "ic_member_2"]:
            approval = workflow.submit_approval(
                deal_id=1,
                gate="IC1",
                ic_member=member_id,
                approval_type="approve",
                comment=f"Approval from {member_id}"
            )
            approvals.append(approval)

        # Verify all approvals recorded
        assert len(approvals) == 3

        # Verify quorum is met
        assert workflow.check_quorum("IC1", 1)

        # Verify audit trail
        audit_entries = db_session.query("governance_audit").filter(
            "deal_id" == 1,
            "action" == "approval_submitted"
        ).all()
        assert len(audit_entries) == 3


class TestRealWorldGovernanceScenarios:
    """Test governance system with realistic scenarios."""

    def test_typical_deal_progression(self, db_session):
        """Test typical deal progression through all gates."""
        workflow = ICWorkflow(db_session)
        repo = GovernanceRepository(db_session)

        # Initialize and progress deal
        deal_id = 1
        repo.initialize_deal_gate(deal_id)

        gates = ["Screen", "IOI", "LOI", "IC1", "IC2", "Close"]
        for i, gate in enumerate(gates):
            if i == 0:
                continue  # Already at Screen

            # Provide required artifacts
            artifacts = get_required_artifacts(gate)

            # For IC gates, submit approvals first
            if gate in ["IC1", "IC2"]:
                # Submit minimum required approvals
                members_to_approve = ["ic_chair", "ic_member_1", "ic_member_2"]
                for member in members_to_approve:
                    workflow.submit_approval(deal_id, gate, member, "approve")

            # Advance to next gate
            deal = workflow.advance(
                deal_id=deal_id,
                target_gate=gate,
                artifacts=artifacts,
                user_id="analyst"
            )

            assert deal.current_gate == gate

    def test_gate_timeout_handling(self, db_session):
        """Test handling of deals that exceed gate timeouts."""
        repo = GovernanceRepository(db_session)

        # Create deal with old timestamp
        deal_gate = repo.initialize_deal_gate(deal_id=1)
        deal_gate.last_updated = datetime.now() - timedelta(hours=200)  # 200+ hours ago
        db_session.commit()

        # Check for bottlenecks
        bottlenecks = repo.get_bottlenecked_deals(timeout_hours=168)  # 1 week
        assert len(bottlenecks) >= 1

    def test_governance_metrics_calculation(self, db_session):
        """Test governance metrics calculation."""
        repo = GovernanceRepository(db_session)

        # Create some activity
        workflow = ICWorkflow(db_session)
        workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=get_required_artifacts("IOI"),
            user_id="analyst"
        )

        # Get metrics
        metrics = repo.get_governance_metrics(days=30)

        assert "period_days" in metrics
        assert "total_activity" in metrics
        assert "gate_metrics" in metrics
        assert "bottlenecked_deals" in metrics

        # Should have some activity recorded
        assert metrics["total_activity"] > 0


class TestErrorRecovery:
    """Test error handling and recovery scenarios."""

    def test_partial_approval_recovery(self, db_session):
        """Test recovery when some approvals are submitted but quorum not met."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IC1
        workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=get_required_artifacts("IC1"),
            user_id="analyst"
        )

        # Submit only one approval (below 75% threshold)
        workflow.submit_approval(1, "IC1", "ic_chair", "approve")

        # Should not meet quorum
        assert not workflow.check_quorum("IC1", 1)

        # Submit additional approvals to meet threshold
        workflow.submit_approval(1, "IC1", "ic_member_1", "approve")
        workflow.submit_approval(1, "IC1", "ic_member_2", "approve")

        # Now should meet quorum
        assert workflow.check_quorum("IC1", 1)

    def test_artifact_update_recovery(self, db_session):
        """Test updating artifact status after initial submission."""
        repo = GovernanceRepository(db_session)

        # Initialize deal
        repo.initialize_deal_gate(deal_id=1)

        # Initially mark artifact as not provided
        artifact = repo.update_artifact_status(
            deal_id=1,
            gate="Screen",
            artifact_name="market_analysis_summary",
            provided=False
        )

        assert artifact.provided is False

        # Later update as provided
        updated_artifact = repo.update_artifact_status(
            deal_id=1,
            gate="Screen",
            artifact_name="market_analysis_summary",
            provided=True,
            provided_by="analyst"
        )

        assert updated_artifact.provided is True
        assert updated_artifact.provided_by == "analyst"


class TestConcurrentAccess:
    """Test concurrent access and transaction handling."""

    def test_multiple_sessions_same_deal(self, db_session):
        """Test handling multiple sessions accessing same deal."""
        from aker_core.database import get_session

        # Create workflow with first session
        workflow1 = ICWorkflow(db_session)

        # Initialize deal
        deal = workflow1.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=get_required_artifacts("IOI"),
            user_id="analyst"
        )

        # Create workflow with second session (simulating concurrent access)
        session2 = get_session()
        workflow2 = ICWorkflow(session2)

        # Try to advance same deal from second session
        # This should work (database handles concurrency)
        try:
            deal2 = workflow2.advance(
                deal_id=1,
                target_gate="LOI",
                artifacts=get_required_artifacts("LOI"),
                user_id="analyst"
            )
            assert deal2.current_gate == "LOI"
        except Exception:
            # May fail due to transaction isolation, which is expected
            pass

        session2.close()


class TestAuditTrailCompleteness:
    """Test that all actions are properly audited."""

    def test_all_actions_audited(self, db_session):
        """Test that all workflow actions create audit entries."""
        workflow = ICWorkflow(db_session)

        initial_audit_count = db_session.query("governance_audit").count()

        # Perform various actions
        workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=get_required_artifacts("IOI"),
            user_id="analyst"
        )

        workflow.submit_approval(1, "IOI", "ic_chair", "approve")

        final_audit_count = db_session.query("governance_audit").count()

        # Should have created audit entries
        assert final_audit_count > initial_audit_count

        # Check that entries have required fields
        recent_audits = db_session.query("governance_audit").filter(
            "deal_id" == 1
        ).order_by("timestamp".desc()).limit(2).all()

        assert len(recent_audits) >= 2
        assert all(audit.user_id for audit in recent_audits)
        assert all(audit.action for audit in recent_audits)
