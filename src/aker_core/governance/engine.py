from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .config import (
    get_gate_definition,
    get_ic_members,
    get_ic_quorum_threshold,
    validate_gate_transition,
)
from .models import DealGate, GateArtifact, GovernanceAudit, ICApproval


class ICWorkflow:
    """Investment Committee workflow engine with state machine management."""

    def __init__(self, session: Session):
        self.session = session

    def advance(
        self,
        deal_id: int,
        target_gate: str,
        artifacts: List[str],
        user_id: str,
        comment: Optional[str] = None
    ) -> DealGate:
        """Advance deal to next gate with artifact validation.

        Args:
            deal_id: ID of the deal to advance
            target_gate: Target gate to advance to
            artifacts: List of provided artifact names
            user_id: User performing the action
            comment: Optional comment for the action

        Returns:
            Updated DealGate object

        Raises:
            ValueError: If transition is invalid or artifacts are missing
        """
        # Get current deal state
        current_gate = self.session.get(DealGate, deal_id)
        if current_gate is None:
            # Initialize new deal at Screen gate
            current_gate = DealGate(
                deal_id=deal_id,
                current_gate="Screen",
                entered_at=datetime.now()
            )
            self.session.add(current_gate)
        else:
            # Validate gate transition
            if not validate_gate_transition(current_gate.current_gate, target_gate):
                raise ValueError(
                    f"Invalid gate transition: {current_gate.current_gate} -> {target_gate}"
                )

        # Validate artifacts for target gate
        required_artifacts = get_gate_definition(target_gate).required_artifacts
        missing_artifacts = [art for art in required_artifacts if art not in artifacts]

        if missing_artifacts:
            raise ValueError(
                f"Missing required artifacts for {target_gate}: {missing_artifacts}"
            )

        # Update deal state
        current_gate.current_gate = target_gate
        current_gate.last_updated = datetime.now()

        # Create artifacts records
        self._create_artifact_records(deal_id, target_gate, artifacts, user_id)

        # Log audit entry
        self._log_audit_entry(
            deal_id=deal_id,
            action="gate_advance",
            gate=target_gate,
            user_id=user_id,
            details={
                "from_gate": current_gate.current_gate,
                "to_gate": target_gate,
                "artifacts_provided": artifacts,
                "comment": comment
            }
        )

        self.session.commit()
        return current_gate

    def submit_approval(
        self,
        deal_id: int,
        gate: str,
        ic_member: str,
        approval_type: str,
        comment: Optional[str] = None,
        user_id: str = ""
    ) -> ICApproval:
        """Submit IC approval for a deal gate.

        Args:
            deal_id: ID of the deal
            gate: Gate being voted on
            ic_member: IC member submitting the approval
            approval_type: 'approve', 'reject', or 'abstain'
            comment: Optional comment
            user_id: User performing the action

        Returns:
            Created ICApproval record

        Raises:
            ValueError: If approval type is invalid or quorum not met
        """
        if approval_type not in ['approve', 'reject', 'abstain']:
            raise ValueError(f"Invalid approval type: {approval_type}")

        # Get deal and validate it's in the correct gate
        deal_gate = self.session.get(DealGate, deal_id)
        if deal_gate is None or deal_gate.current_gate != gate:
            raise ValueError(f"Deal {deal_id} is not in gate {gate}")

        # Check if IC member has already voted
        existing_vote = self.session.query(ICApproval).filter(
            ICApproval.deal_id == deal_id,
            ICApproval.gate == gate,
            ICApproval.ic_member == ic_member
        ).first()

        if existing_vote:
            # Update existing vote
            existing_vote.approval_type = approval_type
            existing_vote.comment = comment
            existing_vote.approved_at = datetime.now()
            approval = existing_vote
        else:
            # Create new approval
            approval = ICApproval(
                deal_id=deal_id,
                gate=gate,
                ic_member=ic_member,
                approval_type=approval_type,
                comment=comment,
                voting_weight=self._get_ic_member_weight(ic_member)
            )
            self.session.add(approval)

        # Log audit entry
        self._log_audit_entry(
            deal_id=deal_id,
            action="approval_submitted",
            gate=gate,
            user_id=user_id or ic_member,
            details={
                "ic_member": ic_member,
                "approval_type": approval_type,
                "comment": comment
            }
        )

        self.session.commit()
        return approval

    def check_gate_completion(self, deal_id: int, gate: str) -> bool:
        """Check if a deal gate is complete (all artifacts provided and approvals met)."""
        deal_gate = self.session.get(DealGate, deal_id)
        if deal_gate is None or deal_gate.current_gate != gate:
            return False

        # Check if all required artifacts are provided
        required_artifacts = get_gate_definition(gate).required_artifacts
        provided_artifacts = self.session.query(GateArtifact).filter(
            GateArtifact.deal_id == deal_id,
            GateArtifact.gate == gate,
            GateArtifact.provided
        ).all()

        provided_names = [art.artifact_name for art in provided_artifacts]

        if not all(art in provided_names for art in required_artifacts):
            return False

        # For gates requiring quorum, check approval status
        gate_def = get_gate_definition(gate)
        if gate_def.quorum_required:
            return self._check_approval_quorum(deal_id, gate)

        return True

    def get_required_artifacts(self, gate: str) -> List[str]:
        """Get required artifacts for a specific gate."""
        return get_gate_definition(gate).required_artifacts

    def check_quorum(self, gate: str, deal_id: int) -> bool:
        """Check if quorum requirements are met for a gate."""
        return self._check_approval_quorum(deal_id, gate)

    def _create_artifact_records(
        self,
        deal_id: int,
        gate: str,
        artifacts: List[str],
        user_id: str
    ):
        """Create artifact records for a gate."""
        required_artifacts = get_gate_definition(gate).required_artifacts

        for artifact_name in required_artifacts:
            provided = artifact_name in artifacts
            provided_at = datetime.now() if provided else None
            provided_by = user_id if provided else None

            artifact = GateArtifact(
                deal_id=deal_id,
                gate=gate,
                artifact_type="document",
                artifact_name=artifact_name,
                required=True,
                provided=provided,
                provided_at=provided_at,
                provided_by=provided_by
            )
            self.session.add(artifact)

    def _check_approval_quorum(self, deal_id: int, gate: str) -> bool:
        """Check if approval quorum is met for a gate."""
        # Get all approvals for this deal and gate
        approvals = self.session.query(ICApproval).filter(
            ICApproval.deal_id == deal_id,
            ICApproval.gate == gate
        ).all()

        if not approvals:
            return False

        # Calculate total voting weight and approval weight
        ic_members = get_ic_members()
        total_weight = sum(member.voting_weight for member in ic_members.values())
        approval_weight = sum(
            approval.voting_weight
            for approval in approvals
            if approval.approval_type == 'approve'
        )

        # Check if we meet the threshold
        threshold = get_ic_quorum_threshold(gate)
        return (approval_weight / total_weight) >= threshold

    def _get_ic_member_weight(self, ic_member: str) -> float:
        """Get the voting weight for an IC member."""
        ic_members = get_ic_members()
        member = ic_members.get(ic_member)
        return member.voting_weight if member else 1.0

    def _log_audit_entry(
        self,
        deal_id: int,
        action: str,
        gate: Optional[str] = None,
        user_id: str = "",
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an audit entry for governance actions."""
        audit_entry = GovernanceAudit(
            deal_id=deal_id,
            action=action,
            gate=gate,
            user_id=user_id,
            details=json.dumps(details) if details else None,
            timestamp=datetime.now()
        )
        self.session.add(audit_entry)


# Convenience functions for direct use
def advance(
    deal_id: int,
    target_gate: str,
    artifacts: List[str],
    user_id: str,
    comment: Optional[str] = None,
    session: Optional[Session] = None
) -> DealGate:
    """Advance a deal to the next gate."""
    if session is None:
        from aker_core.database import get_session
        session = get_session()

    workflow = ICWorkflow(session)
    return workflow.advance(deal_id, target_gate, artifacts, user_id, comment)


def get_required_artifacts(gate: str) -> List[str]:
    """Get required artifacts for a specific gate."""
    return get_gate_definition(gate).required_artifacts


def check_quorum(gate: str, deal_id: int, session: Optional[Session] = None) -> bool:
    """Check if quorum requirements are met for a gate."""
    if session is None:
        from aker_core.database import get_session
        session = get_session()

    workflow = ICWorkflow(session)
    return workflow.check_quorum(gate, deal_id)
