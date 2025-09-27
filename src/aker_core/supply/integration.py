"""
Supply Calculator Integration Module

Provides high-level functions for calculating and persisting supply constraint metrics.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..database.supply import SupplyRepository
from .elasticity import elasticity
from .leaseup import leaseup_tom
from .vacancy import vacancy


def calculate_supply_metrics(
    session: Session,
    msa_id: str,
    permits_data: list[float],
    households_data: list[float],
    hud_vacancy_data: dict,
    lease_data: dict,
    data_vintage: str,
    run_id: Optional[int] = None,
    years: int = 3,
    time_window_days: int = 90,
) -> Dict[str, Any]:
    """
    Calculate all supply constraint metrics for an MSA and persist to database.

    Args:
        session: SQLAlchemy session
        msa_id: MSA identifier
        permits_data: List of annual building permit counts
        households_data: List of annual household counts
        hud_vacancy_data: HUD vacancy data dictionary
        lease_data: Lease transaction data dictionary
        data_vintage: Data vintage string (YYYY-MM-DD)
        run_id: Optional run identifier for lineage tracking
        years: Number of years for elasticity averaging
        time_window_days: Days for lease-up analysis window

    Returns:
        Dictionary with calculated metrics and database record info
    """
    repo = SupplyRepository(session)

    # Calculate elasticity
    elasticity_value = elasticity(permits_data, households_data, years=years)
    elasticity_run_id = run_id

    # Calculate vacancy
    vacancy_value = vacancy(hud_vacancy_data)
    vacancy_run_id = run_id

    # Calculate lease-up time
    leaseup_value = leaseup_tom(lease_data, time_window_days=time_window_days)
    leaseup_run_id = run_id

    # Create data hash for lineage tracking
    data_hash_input = json.dumps(
        {
            "msa_id": msa_id,
            "permits": permits_data,
            "households": households_data,
            "hud_data": hud_vacancy_data,
            "lease_data": lease_data,
            "years": years,
            "time_window": time_window_days,
        },
        sort_keys=True,
    )

    data_hash = hashlib.sha256(data_hash_input.encode()).hexdigest()

    # Create database record
    record = repo.create(
        msa_id=msa_id,
        data_vintage=data_vintage,
        elasticity_idx=elasticity_value,
        elasticity_years=years,
        elasticity_run_id=elasticity_run_id,
        vacancy_rate=vacancy_value,
        vacancy_type=hud_vacancy_data.get("vacancy_type", "rental"),
        vacancy_source=hud_vacancy_data.get("source", "HUD"),
        vacancy_run_id=vacancy_run_id,
        leaseup_tom_days=leaseup_value,
        leaseup_sample_size=len(lease_data.get("lease_date", [])),
        leaseup_time_window_days=time_window_days,
        leaseup_run_id=leaseup_run_id,
        source_data_hash=data_hash,
        calculation_version="1.0.0",
    )

    return {
        "record_id": record.id,
        "elasticity": elasticity_value,
        "vacancy": vacancy_value,
        "leaseup_days": leaseup_value,
        "data_hash": data_hash,
        "calculation_timestamp": record.calculation_timestamp,
    }


def get_supply_scores_for_scoring(
    session: Session, msa_id: str, as_of: Optional[date] = None
) -> Dict[str, float]:
    """
    Get supply constraint scores formatted for pillar scoring.

    Returns normalized scores (0-100) where:
    - Higher elasticity/vacancy/lease-up = Lower constraint scores
    - Inverse relationships applied for scoring pipeline

    Args:
        session: SQLAlchemy session
        msa_id: MSA identifier
        as_of: Optional cutoff date for data vintage

    Returns:
        Dictionary with supply constraint scores
    """
    repo = SupplyRepository(session)

    # Get latest supply metrics
    record = repo.get_by_msa_and_date(msa_id, "latest", as_of)

    if not record:
        raise ValueError(f"No supply metrics found for MSA {msa_id}")

    # Apply inverse scoring logic
    from .elasticity import inverse_elasticity_score
    from .leaseup import inverse_leaseup_score
    from .vacancy import inverse_vacancy_score

    elasticity_score = inverse_elasticity_score(record.elasticity_idx or 0)
    vacancy_score = inverse_vacancy_score(record.vacancy_rate or 0)
    leaseup_score = inverse_leaseup_score(record.leaseup_tom_days or 90)

    return {
        "elasticity_score": elasticity_score,
        "vacancy_score": vacancy_score,
        "leaseup_score": leaseup_score,
        "composite_supply_score": (elasticity_score + vacancy_score + leaseup_score) / 3,
    }


def validate_supply_data_quality(
    session: Session, msa_ids: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Validate supply metrics data quality using Great Expectations.

    Args:
        session: SQLAlchemy session
        msa_ids: Optional list of MSA IDs to validate

    Returns:
        Validation results summary
    """
    repo = SupplyRepository(session)
    stats = repo.get_supply_summary_stats(msa_ids)

    # Basic quality checks
    quality_checks = {
        "total_records": stats["total_records"] > 0,
        "has_elasticity_data": stats["avg_elasticity"] is not None,
        "has_vacancy_data": stats["avg_vacancy"] is not None,
        "has_leaseup_data": stats["avg_leaseup_days"] is not None,
        "data_freshness": (
            (datetime.now() - stats["latest_calc"]).days < 30 if stats["latest_calc"] else False
        ),
    }

    return {
        "quality_checks": quality_checks,
        "summary_stats": stats,
        "overall_quality": all(quality_checks.values()),
    }
