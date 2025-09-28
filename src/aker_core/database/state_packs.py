from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from aker_data.models_extra import StateRules


class StatePacksRepository:
    """Repository for state rule pack persistence and audit trails."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_rule_application(
        self,
        *,
        state_code: str,
        rule_version: str,
        rule_snapshot: dict,
        context_hash: str,
        applied_at: datetime | None = None
    ) -> StateRules:
        """Save a state rule application snapshot for audit trails.

        Args:
            state_code: Two-letter state code
            rule_version: Version of the rule pack applied
            rule_snapshot: JSON snapshot of applied rules
            context_hash: Hash of the context for change detection
            applied_at: When the rules were applied (defaults to now)

        Returns:
            Created StateRules record
        """
        if applied_at is None:
            applied_at = datetime.now()

        rule_record = StateRules(
            state_code=state_code,
            rule_version=rule_version,
            rule_snapshot=rule_snapshot,
            context_hash=context_hash,
            applied_at=applied_at
        )

        self.session.add(rule_record)
        self.session.flush()

        return rule_record

    def get_rule_history(
        self,
        state_code: str | None = None,
        limit: int = 100
    ) -> list[StateRules]:
        """Get historical rule applications.

        Args:
            state_code: Filter by state code (optional)
            limit: Maximum number of records to return

        Returns:
            List of StateRules records ordered by application time (newest first)
        """
        query = self.session.query(StateRules)

        if state_code:
            query = query.filter(StateRules.state_code == state_code)

        return query.order_by(StateRules.applied_at.desc()).limit(limit).all()

    def get_context_changes(
        self,
        context_hash: str,
        state_code: str | None = None
    ) -> list[StateRules]:
        """Get all rule applications for a specific context hash.

        Args:
            context_hash: Hash of the context to find applications for
            state_code: Filter by state code (optional)

        Returns:
            List of StateRules records for the context
        """
        query = self.session.query(StateRules).filter(
            StateRules.context_hash == context_hash
        )

        if state_code:
            query = query.filter(StateRules.state_code == state_code)

        return query.order_by(StateRules.applied_at.desc()).all()
