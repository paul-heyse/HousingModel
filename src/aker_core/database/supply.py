"""
Database repository for supply constraint metrics.

Provides CRUD operations for the market_supply table.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from aker_data.models import MarketSupply


class SupplyRepository:
    """Repository for supply constraint metrics."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_msa_and_date(
        self, msa_id: str, data_vintage: str, as_of: Optional[date] = None
    ) -> Optional[MarketSupply]:
        """Get supply metrics for a specific MSA and data vintage."""
        stmt = select(MarketSupply).where(
            and_(MarketSupply.msa_id == msa_id, MarketSupply.data_vintage == data_vintage)
        )

        if as_of:
            stmt = stmt.where(MarketSupply.calculation_timestamp >= as_of)

        return (
            self.session.execute(stmt.order_by(MarketSupply.calculation_timestamp.desc()).limit(1))
            .scalars()
            .first()
        )

    def create(
        self,
        msa_id: str,
        data_vintage: str,
        elasticity_idx: Optional[float] = None,
        elasticity_years: Optional[int] = None,
        elasticity_run_id: Optional[int] = None,
        vacancy_rate: Optional[float] = None,
        vacancy_type: Optional[str] = None,
        vacancy_source: Optional[str] = None,
        vacancy_run_id: Optional[int] = None,
        leaseup_tom_days: Optional[float] = None,
        leaseup_sample_size: Optional[int] = None,
        leaseup_time_window_days: Optional[int] = None,
        leaseup_run_id: Optional[int] = None,
        source_data_hash: Optional[str] = None,
        calculation_version: Optional[str] = None,
    ) -> MarketSupply:
        """Create a new supply metrics record."""
        record = MarketSupply(
            msa_id=msa_id,
            data_vintage=data_vintage,
            elasticity_idx=elasticity_idx,
            elasticity_years=elasticity_years,
            elasticity_run_id=elasticity_run_id,
            vacancy_rate=vacancy_rate,
            vacancy_type=vacancy_type,
            vacancy_source=vacancy_source,
            vacancy_run_id=vacancy_run_id,
            leaseup_tom_days=leaseup_tom_days,
            leaseup_sample_size=leaseup_sample_size,
            leaseup_time_window_days=leaseup_time_window_days,
            leaseup_run_id=leaseup_run_id,
            source_data_hash=source_data_hash,
            calculation_version=calculation_version,
        )

        self.session.add(record)
        self.session.flush()  # Get the ID without committing
        return record

    def get_latest_by_msa(self, msa_id: str) -> Optional[MarketSupply]:
        """Get the most recent supply metrics for an MSA."""
        stmt = (
            select(MarketSupply)
            .where(MarketSupply.msa_id == msa_id)
            .order_by(MarketSupply.calculation_timestamp.desc())
            .limit(1)
        )

        return self.session.execute(stmt).scalars().first()

    def get_by_run_id(self, run_id: int) -> Sequence[MarketSupply]:
        """Get all supply metrics for a specific run."""
        stmt = (
            select(MarketSupply)
            .where(MarketSupply.elasticity_run_id == run_id)
            .union(select(MarketSupply).where(MarketSupply.vacancy_run_id == run_id))
            .union(select(MarketSupply).where(MarketSupply.leaseup_run_id == run_id))
        )

        return self.session.execute(stmt).scalars().all()

    def get_supply_summary_stats(self, msa_ids: Optional[list[str]] = None) -> dict:
        """Get summary statistics for supply metrics across MSAs."""
        query = select(
            func.count(MarketSupply.id).label("total_records"),
            func.avg(MarketSupply.elasticity_idx).label("avg_elasticity"),
            func.avg(MarketSupply.vacancy_rate).label("avg_vacancy"),
            func.avg(MarketSupply.leaseup_tom_days).label("avg_leaseup_days"),
            func.min(MarketSupply.calculation_timestamp).label("earliest_calc"),
            func.max(MarketSupply.calculation_timestamp).label("latest_calc"),
        )

        if msa_ids:
            query = query.where(MarketSupply.msa_id.in_(msa_ids))

        result = self.session.execute(query).first()

        return {
            "total_records": result.total_records or 0,
            "avg_elasticity": float(result.avg_elasticity) if result.avg_elasticity else None,
            "avg_vacancy": float(result.avg_vacancy) if result.avg_vacancy else None,
            "avg_leaseup_days": float(result.avg_leaseup_days) if result.avg_leaseup_days else None,
            "earliest_calc": result.earliest_calc,
            "latest_calc": result.latest_calc,
        }
