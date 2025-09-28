from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from aker_core.governance.config import get_gate_definition, get_ic_members
from ..governance.models import DealGate, GateArtifact, GovernanceAudit, ICApproval


class GovernanceRepository:
    """Repository for governance data access and operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_deal_gate(self, deal_id: int) -> Optional[DealGate]:
        """Get the current gate state for a deal."""
        return self.session.get(DealGate, deal_id)

    def get_deal_artifacts(self, deal_id: int, gate: Optional[str] = None) -> List[GateArtifact]:
        """Get artifacts for a deal, optionally filtered by gate."""
        query = self.session.query(GateArtifact).filter(GateArtifact.deal_id == deal_id)
        if gate:
            query = query.filter(GateArtifact.gate == gate)
        return query.all()

    def get_deal_approvals(self, deal_id: int, gate: Optional[str] = None) -> List[ICApproval]:
        """Get approvals for a deal, optionally filtered by gate."""
        query = self.session.query(ICApproval).filter(ICApproval.deal_id == deal_id)
        if gate:
            query = query.filter(ICApproval.gate == gate)
        return query.all()

    def get_governance_audit(self, deal_id: int, limit: int = 100) -> List[GovernanceAudit]:
        """Get audit trail for a deal."""
        return (
            self.session.query(GovernanceAudit)
            .filter(GovernanceAudit.deal_id == deal_id)
            .order_by(GovernanceAudit.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_deals_in_gate(self, gate: str) -> List[DealGate]:
        """Get all deals currently in a specific gate."""
        return (
            self.session.query(DealGate)
            .filter(DealGate.current_gate == gate)
            .all()
        )

    def get_gate_completion_status(self, deal_id: int, gate: str) -> Dict[str, Any]:
        """Get detailed completion status for a deal gate."""
        deal_gate = self.get_deal_gate(deal_id)
        if not deal_gate or deal_gate.current_gate != gate:
            return {"status": "not_in_gate", "progress": 0.0}

        # Get required artifacts
        required_artifacts = get_gate_definition(gate).required_artifacts

        # Get provided artifacts
        provided_artifacts = [
            art for art in self.get_deal_artifacts(deal_id, gate)
            if art.provided
        ]

        artifact_progress = len(provided_artifacts) / len(required_artifacts)

        # Check approval status for gates requiring quorum
        gate_def = get_gate_definition(gate)
        if gate_def.quorum_required:
            approvals = self.get_deal_approvals(deal_id, gate)
            ic_members = get_ic_members()
            total_weight = sum(member.voting_weight for member in ic_members.values())
            approval_weight = sum(
                approval.voting_weight
                for approval in approvals
                if approval.approval_type == 'approve'
            )

            approval_progress = approval_weight / total_weight if total_weight > 0 else 0.0
            threshold = gate_def.approval_threshold

            if approval_progress >= threshold:
                status = "complete"
            else:
                status = "pending_approvals"
        else:
            if artifact_progress >= 1.0:
                status = "complete"
            else:
                status = "pending_artifacts"

        return {
            "status": status,
            "artifact_progress": artifact_progress,
            "approval_progress": approval_progress if gate_def.quorum_required else 1.0,
            "required_artifacts": required_artifacts,
            "provided_artifacts": len(provided_artifacts),
            "threshold": gate_def.approval_threshold if gate_def.quorum_required else None
        }

    def get_bottlenecked_deals(self, timeout_hours: int = 168) -> List[DealGate]:
        """Get deals that have been stuck in gates for too long."""
        cutoff_time = datetime.now() - timedelta(hours=timeout_hours)

        return (
            self.session.query(DealGate)
            .filter(DealGate.last_updated < cutoff_time)
            .all()
        )

    def get_governance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get governance performance metrics."""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get recent audit entries
        recent_audits = (
            self.session.query(GovernanceAudit)
            .filter(GovernanceAudit.timestamp >= cutoff_date)
            .all()
        )

        # Calculate metrics by gate
        gate_metrics = {}
        for gate_name in get_gate_definition.__wrapped__("").__self__.keys():
            gate_audits = [a for a in recent_audits if a.gate == gate_name]

            if gate_audits:
                # Calculate average time in gate
                gate_entries = [a for a in gate_audits if a.action == "gate_advance"]
                if len(gate_entries) > 1:
                    times = []
                    for i in range(1, len(gate_entries)):
                        prev_time = gate_entries[i-1].timestamp
                        curr_time = gate_entries[i].timestamp
                        times.append((curr_time - prev_time).total_seconds() / 3600)

                    avg_time = sum(times) / len(times)
                else:
                    avg_time = None

                # Count deals in gate
                deals_in_gate = len(self.get_deals_in_gate(gate_name))

                gate_metrics[gate_name] = {
                    "average_time_hours": avg_time,
                    "deals_in_gate": deals_in_gate,
                    "activity_count": len(gate_audits)
                }

        return {
            "period_days": days,
            "total_activity": len(recent_audits),
            "gate_metrics": gate_metrics,
            "bottlenecked_deals": len(self.get_bottlenecked_deals())
        }

    def initialize_deal_gate(self, deal_id: int) -> DealGate:
        """Initialize a new deal at the Screen gate."""
        deal_gate = DealGate(
            deal_id=deal_id,
            current_gate="Screen",
            entered_at=datetime.now()
        )
        self.session.add(deal_gate)
        self.session.flush()
        return deal_gate

    def update_artifact_status(
        self,
        deal_id: int,
        gate: str,
        artifact_name: str,
        provided: bool,
        provided_by: Optional[str] = None
    ) -> GateArtifact:
        """Update the status of a specific artifact."""
        # Find existing artifact or create new one
        artifact = (
            self.session.query(GateArtifact)
            .filter(
                GateArtifact.deal_id == deal_id,
                GateArtifact.gate == gate,
                GateArtifact.artifact_name == artifact_name
            )
            .first()
        )

        if artifact is None:
            artifact = GateArtifact(
                deal_id=deal_id,
                gate=gate,
                artifact_type="document",
                artifact_name=artifact_name,
                required=True
            )
            self.session.add(artifact)

        artifact.provided = provided
        artifact.provided_at = datetime.now() if provided else None
        artifact.provided_by = provided_by

        self.session.flush()
        return artifact
