from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class GateDefinition:
    """Definition of a governance gate with required artifacts."""
    name: str
    description: str
    required_artifacts: List[str]
    approval_threshold: float = 0.5  # Minimum approval percentage required
    quorum_required: bool = True
    timeout_hours: int = 168  # 1 week default timeout

    def __post_init__(self):
        """Validate gate definition."""
        if not 0.0 <= self.approval_threshold <= 1.0:
            raise ValueError("Approval threshold must be between 0.0 and 1.0")
        if self.timeout_hours <= 0:
            raise ValueError("Timeout hours must be positive")


# Gate sequence: Screen → IOI → LOI → IC1 → IC2 → Close
GATE_DEFINITIONS = {
    "Screen": GateDefinition(
        name="Screen",
        description="Initial deal screening and basic validation",
        required_artifacts=[
            "market_analysis_summary",
            "preliminary_financial_model",
            "asset_overview_document",
            "risk_assessment_checklist"
        ],
        approval_threshold=0.5,
        quorum_required=False,  # Single approver for screening
        timeout_hours=72  # 3 days
    ),
    "IOI": GateDefinition(
        name="IOI",
        description="Indication of Interest with initial due diligence",
        required_artifacts=[
            "detailed_market_analysis",
            "property_condition_assessment",
            "initial_underwriting_model",
            "environmental_screening_report"
        ],
        approval_threshold=0.6,
        quorum_required=True,
        timeout_hours=120  # 5 days
    ),
    "LOI": GateDefinition(
        name="LOI",
        description="Letter of Intent with detailed terms",
        required_artifacts=[
            "executed_loi_document",
            "detailed_financial_projections",
            "legal_due_diligence_summary",
            "insurance_requirements_analysis"
        ],
        approval_threshold=0.7,
        quorum_required=True,
        timeout_hours=96  # 4 days
    ),
    "IC1": GateDefinition(
        name="IC1",
        description="Investment Committee Round 1 review",
        required_artifacts=[
            "complete_underwriting_package",
            "risk_assessment_report",
            "esg_compliance_checklist",
            "portfolio_impact_analysis"
        ],
        approval_threshold=0.75,
        quorum_required=True,
        timeout_hours=168  # 1 week
    ),
    "IC2": GateDefinition(
        name="IC2",
        description="Investment Committee Round 2 final approval",
        required_artifacts=[
            "final_investment_memo",
            "legal_documentation_package",
            "insurance_and_risk_transfer_analysis",
            "exit_strategy_documentation"
        ],
        approval_threshold=0.8,
        quorum_required=True,
        timeout_hours=168  # 1 week
    ),
    "Close": GateDefinition(
        name="Close",
        description="Transaction completion and documentation",
        required_artifacts=[
            "closing_documentation",
            "final_funding_confirmation",
            "post_close_compliance_checklist",
            "performance_tracking_setup"
        ],
        approval_threshold=0.9,
        quorum_required=True,
        timeout_hours=48  # 2 days
    )
}


@dataclass
class ICMember:
    """Investment Committee member definition."""
    user_id: str
    name: str
    role: str
    voting_weight: float = 1.0
    is_active: bool = True


# Default IC composition - can be overridden via configuration
IC_COMPOSITION = {
    "chair": ICMember("ic_chair", "IC Chairperson", "chair", voting_weight=1.5),
    "vice_chair": ICMember("ic_vice_chair", "IC Vice Chairperson", "vice_chair", voting_weight=1.2),
    "members": [
        ICMember("ic_member_1", "Senior Investment Director", "senior_director"),
        ICMember("ic_member_2", "Portfolio Manager", "portfolio_manager"),
        ICMember("ic_member_3", "Risk Officer", "risk_officer"),
        ICMember("ic_member_4", "ESG Specialist", "esg_specialist"),
        ICMember("ic_member_5", "Legal Counsel", "legal_counsel"),
    ]
}


def get_gate_sequence() -> List[str]:
    """Get the valid sequence of gates."""
    return list(GATE_DEFINITIONS.keys())


def get_gate_definition(gate: str) -> GateDefinition:
    """Get the definition for a specific gate."""
    if gate not in GATE_DEFINITIONS:
        raise ValueError(f"Unknown gate: {gate}")
    return GATE_DEFINITIONS[gate]


def validate_gate_transition(current_gate: str, target_gate: str) -> bool:
    """Validate that a gate transition is allowed."""
    gate_sequence = get_gate_sequence()
    try:
        current_index = gate_sequence.index(current_gate)
        target_index = gate_sequence.index(target_gate)

        # Can only move forward in sequence (no skipping)
        return target_index == current_index + 1
    except ValueError:
        return False


def get_ic_quorum_threshold(gate: str) -> float:
    """Get the quorum threshold for a specific gate."""
    return get_gate_definition(gate).approval_threshold


def get_ic_members() -> Dict[str, ICMember]:
    """Get all active IC members."""
    members = {}
    members.update({member.user_id: member for member in IC_COMPOSITION["members"]})
    if IC_COMPOSITION["chair"].is_active:
        members[IC_COMPOSITION["chair"].user_id] = IC_COMPOSITION["chair"]
    if IC_COMPOSITION["vice_chair"].is_active:
        members[IC_COMPOSITION["vice_chair"].user_id] = IC_COMPOSITION["vice_chair"]
    return members
