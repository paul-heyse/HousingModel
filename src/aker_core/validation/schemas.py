"""Pandera schemas for dataset validation."""

from __future__ import annotations

from typing import Dict

import pandera as pa
from pandera import Check, Column

__all__ = [
    "DATASET_SCHEMAS",
    "DATASET_SCHEMA_ALIASES",
    "SUPPLY_SUMMARY_SCHEMA",
    "resolve_schema",
]

AS_OF_REGEX = r"^\d{4}-\d{2}$"
PERMIT_STATUS_VALUES = {
    "pending",
    "approved",
    "denied",
    "under_review",
    "issued",
    "expired",
    "cancelled",
    "completed",
}
PERMIT_TYPE_VALUES = {
    "residential_new",
    "residential_renovation",
    "commercial_new",
    "commercial_renovation",
    "demolition",
    "addition",
    "pool",
    "garage",
    "deck",
    "fence",
    "other",
}

ACS_INCOME_SCHEMA = pa.DataFrameSchema(
    {
        "name": Column(pa.String, nullable=False),
        "b19013_001e": Column(pa.Float64, checks=Check.ge(0), nullable=False),
        "b01003_001e": Column(pa.Float64, checks=Check.ge(0), nullable=False),
        "data_year": Column(pa.Int64, checks=Check.ge(1900), nullable=False),
        "source": Column(pa.String, nullable=False),
        "ingested_at": Column(pa.DateTime, nullable=False),
        "as_of": Column(pa.String, checks=Check.str_matches(AS_OF_REGEX), nullable=False),
    },
    coerce=True,
    strict=False,
)

MARKET_SCORES_SCHEMA = pa.DataFrameSchema(
    {
        "name": Column(pa.String, nullable=False),
        "market_score": Column(pa.Float64, checks=[Check.ge(0), Check.le(100)], nullable=False),
        "market_tier": Column(pa.String, nullable=False),
        "scoring_model": Column(pa.String, nullable=False),
        "scored_at": Column(pa.DateTime, nullable=False),
        "data_year": Column(pa.Int64, nullable=False, checks=Check.ge(1900)),
        "source": Column(pa.String, nullable=False),
    },
    coerce=True,
    strict=False,
)

MARKET_ANALYTICS_SCHEMA = pa.DataFrameSchema(
    {
        "msa_id": Column(pa.String, nullable=False, checks=Check.str_length(5, 12)),
        "market_name": Column(pa.String, nullable=False),
        "population": Column(pa.Int64, checks=Check.ge(0), nullable=True),
        "households": Column(pa.Int64, checks=Check.ge(0), nullable=True),
        "vacancy_rate": Column(pa.Float64, checks=[Check.ge(0), Check.le(100)], nullable=True),
        "permit_per_1k": Column(pa.Float64, nullable=True),
        "tech_cagr": Column(pa.Float64, nullable=True),
        "walk_15_ct": Column(pa.Float64, checks=Check.ge(0), nullable=True),
        "trail_mi_pc": Column(pa.Float64, checks=Check.ge(0), nullable=True),
        "supply_score": Column(pa.Float64, checks=[Check.ge(0), Check.le(5)], nullable=True),
        "jobs_score": Column(pa.Float64, checks=[Check.ge(0), Check.le(5)], nullable=True),
        "urban_score": Column(pa.Float64, checks=[Check.ge(0), Check.le(5)], nullable=True),
        "outdoor_score": Column(pa.Float64, checks=[Check.ge(0), Check.le(5)], nullable=True),
        "composite_score": Column(pa.Float64, checks=[Check.ge(0), Check.le(5)], nullable=True),
        "period_month": Column(pa.DateTime, nullable=False),
        "refreshed_at": Column(pa.DateTime, nullable=False),
        "run_id": Column(pa.Int64, nullable=True),
    },
    coerce=True,
    strict=False,
)

ASSET_PERFORMANCE_SCHEMA = pa.DataFrameSchema(
    {
        "asset_id": Column(pa.Int64, nullable=False),
        "msa_id": Column(pa.String, nullable=False, checks=Check.str_length(5, 12)),
        "units": Column(pa.Int64, checks=Check.ge(0), nullable=True),
        "year_built": Column(pa.Int64, checks=Check.ge(1800), nullable=True),
        "score": Column(pa.Float64, checks=[Check.ge(0), Check.le(100)], nullable=True),
        "market_composite_score": Column(pa.Float64, checks=[Check.ge(0), Check.le(5)], nullable=True),
        "rank_in_market": Column(pa.Int64, checks=Check.ge(0), nullable=True),
        "period_month": Column(pa.DateTime, nullable=False),
        "refreshed_at": Column(pa.DateTime, nullable=False),
        "run_id": Column(pa.Int64, nullable=True),
    },
    coerce=True,
    strict=False,
)

PERMITS_SCHEMA = pa.DataFrameSchema(
    {
        "permit_id": Column(pa.String, nullable=False),
        "permit_type": Column(pa.String, checks=Check.isin(sorted(PERMIT_TYPE_VALUES)), nullable=False),
        "status": Column(pa.String, checks=Check.isin(sorted(PERMIT_STATUS_VALUES)), nullable=False),
        "description": Column(pa.String, nullable=False),
        "application_date": Column(pa.DateTime, nullable=False),
        "issue_date": Column(pa.DateTime, nullable=True),
        "expiration_date": Column(pa.DateTime, nullable=True),
        "completion_date": Column(pa.DateTime, nullable=True),
        "estimated_cost": Column(pa.Float64, checks=Check.ge(0), nullable=True),
        "actual_cost": Column(pa.Float64, checks=Check.ge(0), nullable=True),
        "valuation": Column(pa.Float64, checks=Check.ge(0), nullable=True),
        "address": Column(pa.Object, nullable=False),
        "property_type": Column(pa.String, nullable=True),
        "square_footage": Column(pa.Int64, checks=Check.ge(0), nullable=True),
        "applicant_name": Column(pa.String, nullable=False),
        "applicant_address": Column(pa.String, nullable=True),
        "contractor_name": Column(pa.String, nullable=True),
        "contractor_license": Column(pa.String, nullable=True),
        "source_system": Column(pa.String, nullable=False),
        "source_url": Column(pa.String, nullable=True),
        "collected_at": Column(pa.DateTime, nullable=False),
        "last_updated": Column(pa.DateTime, nullable=False),
        "data_quality_issues": Column(pa.Object, nullable=True),
        "processing_errors": Column(pa.Object, nullable=True),
    },
    coerce=True,
    strict=False,
)

SUPPLY_SUMMARY_SCHEMA = pa.DataFrameSchema(
    {
        "total_records": Column(pa.Int64, checks=Check.ge(0), nullable=False),
        "avg_elasticity": Column(pa.Float64, nullable=True),
        "avg_vacancy": Column(pa.Float64, nullable=True),
        "avg_leaseup_days": Column(pa.Float64, nullable=True),
        "earliest_calc": Column(pa.DateTime, nullable=True),
        "latest_calc": Column(pa.DateTime, nullable=True),
    },
    coerce=True,
    strict=False,
)

DATASET_SCHEMAS: Dict[str, pa.DataFrameSchema] = {
    "acs_income": ACS_INCOME_SCHEMA,
    "market_scores": MARKET_SCORES_SCHEMA,
    "market_analytics": MARKET_ANALYTICS_SCHEMA,
    "asset_performance": ASSET_PERFORMANCE_SCHEMA,
    "permits": PERMITS_SCHEMA,
    "supply_summary": SUPPLY_SUMMARY_SCHEMA,
    "boundaries": pa.DataFrameSchema(
        {
            "geometry": Column(pa.Object, nullable=False),
            "source_id": Column(pa.String, nullable=False),
            "as_of": Column(pa.String, checks=Check.str_matches(AS_OF_REGEX), nullable=False),
            "ingested_at": Column(pa.DateTime, nullable=False),
        },
        coerce=False,
        strict=False,
    ),
    "geocoding": pa.DataFrameSchema(
        {
            "latitude": Column(pa.Float64, nullable=True),
            "longitude": Column(pa.Float64, nullable=True),
            "confidence": Column(pa.Float64, checks=[Check.ge(0), Check.le(1)], nullable=False),
            "provider": Column(pa.String, nullable=False),
            "as_of": Column(pa.String, checks=Check.str_matches(AS_OF_REGEX), nullable=False),
            "ingested_at": Column(pa.DateTime, nullable=False),
        },
        coerce=True,
        strict=False,
    ),
}

DATASET_SCHEMA_ALIASES: Dict[str, str] = {
    "acs": "acs_income",
    "census": "acs_income",
    "market_data": "market_scores",
    "market_scores": "market_scores",
    "market_analytics": "market_analytics",
    "asset_performance": "asset_performance",
    "permits": "permits",
    "supply_metrics": "supply_summary",
    "supply_summary": "supply_summary",
    "boundary": "boundaries",
    "boundaries": "boundaries",
    "geocode": "geocoding",
    "geocoding": "geocoding",
}


def resolve_schema(dataset_type: str) -> pa.DataFrameSchema:
    """Resolve the Pandera schema for a dataset type."""
    key = dataset_type.lower()
    canonical = DATASET_SCHEMA_ALIASES.get(key, key)
    schema = DATASET_SCHEMAS.get(canonical)
    if schema is None:
        raise KeyError(f"No validation schema registered for dataset type '{dataset_type}'")
    return schema
