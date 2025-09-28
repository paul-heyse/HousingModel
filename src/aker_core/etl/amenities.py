"""ETL helpers for amenity ROI benchmarks."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Optional, Sequence

import pandas as pd

from aker_data.amenities import AmenityBenchmark, AmenityBenchmarkStore

from ..amenities.benchmarks import DEFAULT_AMENITY_CALIBRATIONS, seed_default_benchmarks

logger = logging.getLogger(__name__)


def load_vendor_benchmarks(
    *,
    records: Optional[Sequence[dict[str, object]]] = None,
    as_of: Optional[str] = None,
    store: Optional[AmenityBenchmarkStore] = None,
) -> pd.DataFrame:
    """Load vendor cost/utilisation benchmarks into the shared store."""

    target = store or AmenityBenchmarkStore.instance()
    if not target.list_codes():
        seed_default_benchmarks(target)

    if records is None:
        records = [
            {
                "amenity_code": cal.code,
                "amenity_name": cal.name,
                "rent_premium_per_unit": cal.rent_premium_per_unit,
                "retention_delta_bps": cal.retention_delta_bps,
                "membership_revenue_monthly": cal.membership_revenue_monthly,
                "avg_monthly_rent": cal.avg_monthly_rent,
                "utilization_rate": cal.utilization_rate,
                "opex_monthly": cal.opex_monthly,
                "capex": cal.capex,
                "source": cal.source,
            }
            for cal in DEFAULT_AMENITY_CALIBRATIONS.values()
        ]

    data_vintage = as_of or datetime.now(UTC).strftime("%Y-%m")
    benchmarks = []
    for record in records:
        benchmark = AmenityBenchmark(
            amenity_code=str(record["amenity_code"]).lower(),
            amenity_name=str(record.get("amenity_name", "")).title() or str(record["amenity_code"]).replace("_", " ").title(),
            rent_premium_per_unit=float(record.get("rent_premium_per_unit", 0.0)),
            retention_delta_bps=float(record.get("retention_delta_bps", 0.0)),
            membership_revenue_monthly=float(record.get("membership_revenue_monthly", 0.0)),
            avg_monthly_rent=float(record.get("avg_monthly_rent", 2000.0)),
            utilization_rate=float(record.get("utilization_rate", 0.6)),
            opex_monthly=float(record.get("opex_monthly", 0.0)),
            data_vintage=data_vintage,
            source=str(record.get("source", "vendor")),
            metadata={"default_capex": float(record.get("capex", 0.0))},
        )
        benchmarks.append(benchmark)
    target.ingest(benchmarks)

    df = pd.DataFrame(
        [
            {
                "amenity_code": b.amenity_code,
                "amenity_name": b.amenity_name,
                "rent_premium_per_unit": b.rent_premium_per_unit,
                "retention_delta_bps": b.retention_delta_bps,
                "membership_revenue_monthly": b.membership_revenue_monthly,
                "avg_monthly_rent": b.avg_monthly_rent,
                "utilization_rate": b.utilization_rate,
                "opex_monthly": b.opex_monthly,
                "capex": b.metadata.get("default_capex", 0.0),
                "data_vintage": b.data_vintage,
                "source": b.source,
            }
            for b in benchmarks
        ]
    )
    logger.info("Loaded %s amenity benchmark records", len(df))
    return df


def load_membership_revenue(
    *,
    revenue_rows: Optional[Sequence[dict[str, object]]] = None,
    as_of: Optional[str] = None,
    store: Optional[AmenityBenchmarkStore] = None,
) -> pd.DataFrame:
    """Aggregate membership revenue benchmarks and update amenity store."""

    target = store or AmenityBenchmarkStore.instance()
    if not target.list_codes():
        seed_default_benchmarks(target)

    if revenue_rows is None:
        revenue_rows = [
            {"amenity_code": "cowork_lounge", "monthly_revenue": 1400.0, "utilization": 0.58},
            {"amenity_code": "fitness_center", "monthly_revenue": 520.0, "utilization": 0.7},
            {"amenity_code": "pet_spa", "monthly_revenue": 740.0, "utilization": 0.63},
        ]

    df = pd.DataFrame(revenue_rows)
    grouped = df.groupby("amenity_code", as_index=False).agg(
        monthly_revenue=("monthly_revenue", "mean"), utilization=("utilization", "mean")
    )

    for _, row in grouped.iterrows():
        benchmark = target.get(str(row["amenity_code"]))
        if benchmark:
            updated = AmenityBenchmark(
                amenity_code=benchmark.amenity_code,
                amenity_name=benchmark.amenity_name,
                rent_premium_per_unit=benchmark.rent_premium_per_unit,
                retention_delta_bps=benchmark.retention_delta_bps,
                membership_revenue_monthly=float(row["monthly_revenue"]),
                avg_monthly_rent=benchmark.avg_monthly_rent,
                utilization_rate=float(row["utilization"]),
                opex_monthly=benchmark.opex_monthly,
                data_vintage=as_of or benchmark.data_vintage,
                source=f"{benchmark.source};membership",
                metadata=benchmark.metadata,
            )
            target.ingest([updated])

    logger.info("Loaded amenity membership revenue for %s amenities", len(grouped))
    grouped["as_of"] = as_of or datetime.now(UTC).strftime("%Y-%m")
    return grouped


def load_retention_signals(
    *,
    retention_rows: Optional[Sequence[dict[str, object]]] = None,
    as_of: Optional[str] = None,
    store: Optional[AmenityBenchmarkStore] = None,
) -> pd.DataFrame:
    """Load retention deltas attributable to amenities and merge into benchmarks."""

    target = store or AmenityBenchmarkStore.instance()
    if not target.list_codes():
        seed_default_benchmarks(target)

    if retention_rows is None:
        retention_rows = [
            {"amenity_code": "cowork_lounge", "retention_delta_bps": 190.0},
            {"amenity_code": "fitness_center", "retention_delta_bps": 155.0},
            {"amenity_code": "pet_spa", "retention_delta_bps": 135.0},
        ]

    df = pd.DataFrame(retention_rows)
    for _, row in df.iterrows():
        code = str(row["amenity_code"])
        benchmark = target.get(code)
        if benchmark:
            updated = AmenityBenchmark(
                amenity_code=benchmark.amenity_code,
                amenity_name=benchmark.amenity_name,
                rent_premium_per_unit=benchmark.rent_premium_per_unit,
                retention_delta_bps=float(row["retention_delta_bps"]),
                membership_revenue_monthly=benchmark.membership_revenue_monthly,
                avg_monthly_rent=benchmark.avg_monthly_rent,
                utilization_rate=benchmark.utilization_rate,
                opex_monthly=benchmark.opex_monthly,
                data_vintage=as_of or benchmark.data_vintage,
                source=f"{benchmark.source};retention",
                metadata=benchmark.metadata,
            )
            target.ingest([updated])

    df["as_of"] = as_of or datetime.now(UTC).strftime("%Y-%m")
    logger.info("Loaded amenity retention signals for %s amenities", len(df))
    return df


__all__ = [
    "load_vendor_benchmarks",
    "load_membership_revenue",
    "load_retention_signals",
]
