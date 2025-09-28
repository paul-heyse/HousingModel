from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class DealGate(Base):
    """Deal state machine tracking current gate and progression."""
    __tablename__ = "deal_gates"

    deal_id = Column(Integer, primary_key=True)
    current_gate = Column(String(20), nullable=False)
    entered_at = Column(DateTime, nullable=False, default=datetime.now)
    last_updated = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Relationships
    artifacts = relationship("GateArtifact", back_populates="deal_gate", cascade="all, delete-orphan")
    approvals = relationship("ICApproval", back_populates="deal_gate", cascade="all, delete-orphan")
    audit_entries = relationship("GovernanceAudit", back_populates="deal_gate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DealGate(deal_id={self.deal_id}, gate={self.current_gate})>"


class GateArtifact(Base):
    """Track artifacts required and provided for each gate."""
    __tablename__ = "gate_artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deal_gates.deal_id"), nullable=False)
    gate = Column(String(20), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    artifact_name = Column(String(200), nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    provided = Column(Boolean, nullable=False, default=False)
    provided_at = Column(DateTime, nullable=True)
    provided_by = Column(String(100), nullable=True)
    artifact_hash = Column(String(64), nullable=True)  # For change detection

    # Relationships
    deal_gate = relationship("DealGate", back_populates="artifacts")

    def __repr__(self):
        return f"<GateArtifact(deal_id={self.deal_id}, gate={self.gate}, artifact={self.artifact_name})>"


class ICApproval(Base):
    """Track IC member approvals and voting for each gate."""
    __tablename__ = "ic_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deal_gates.deal_id"), nullable=False)
    gate = Column(String(20), nullable=False)
    ic_member = Column(String(100), nullable=False)
    approval_type = Column(String(20), nullable=False)  # 'approve', 'reject', 'abstain'
    comment = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=False, default=datetime.now)
    voting_weight = Column(Float, nullable=False, default=1.0)

    # Relationships
    deal_gate = relationship("DealGate", back_populates="approvals")

    def __repr__(self):
        return f"<ICApproval(deal_id={self.deal_id}, gate={self.gate}, member={self.ic_member}, type={self.approval_type})>"


class GovernanceAudit(Base):
    """Complete audit trail for all governance actions."""
    __tablename__ = "governance_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deal_gates.deal_id"), nullable=False)
    action = Column(String(50), nullable=False)
    gate = Column(String(20), nullable=True)
    user_id = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)  # JSON string for structured data
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    deal_gate = relationship("DealGate", back_populates="audit_entries")

    def __repr__(self):
        return f"<GovernanceAudit(deal_id={self.deal_id}, action={self.action}, user={self.user_id})>"


# Additional utility models for governance reporting
class DealProgress(Base):
    """Track overall deal progression metrics."""
    __tablename__ = "deal_progress"

    deal_id = Column(Integer, primary_key=True)
    total_gates = Column(Integer, nullable=False, default=6)
    completed_gates = Column(Integer, nullable=False, default=0)
    current_gate = Column(String(20), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.now)
    estimated_completion = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<DealProgress(deal_id={self.deal_id}, progress={self.completed_gates}/{self.total_gates})>"


class GovernanceMetrics(Base):
    """Store governance performance metrics."""
    __tablename__ = "governance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(DateTime, nullable=False)
    gate = Column(String(20), nullable=False)
    average_time_hours = Column(Float, nullable=True)
    approval_rate = Column(Float, nullable=True)
    bottleneck_count = Column(Integer, nullable=False, default=0)
    deals_in_gate = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<GovernanceMetrics(gate={self.gate}, date={self.metric_date})>"
