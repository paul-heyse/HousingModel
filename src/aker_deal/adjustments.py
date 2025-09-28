from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Optional, Sequence

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.lake import DataLake
from aker_data.models import Assets

from .ranking import rank_scopes
from .types import RankConfig, RankedScope, ScopeTemplate


def _latest_partition_as_of(lake: DataLake, dataset: str) -> Optional[str]:
    try:
        parts = lake.list_partitions(dataset)
        as_of_values = [p.split("=", 1)[1] for p in parts if p.startswith("as_of=")]
        return max(as_of_values) if as_of_values else None
    except Exception:
        return None


def _safe_read(lake: DataLake, dataset: str, *, as_of: Optional[str], filters: Optional[Dict[str, object]] = None) -> pd.DataFrame:
    try:
        if as_of is None:
            as_of = _latest_partition_as_of(lake, dataset)
        return lake.read(dataset, as_of=as_of, filters=filters)
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _resolve_msa_id(session: Optional[Session], asset_id: str, provided_msa_id: Optional[str]) -> Optional[str]:
    if provided_msa_id:
        return provided_msa_id
    if session is None:
        return None
    try:
        row = session.execute(select(Assets.msa_id).where(Assets.asset_id == int(asset_id))).first()
        return row[0] if row and row[0] else None
    except Exception:
        return None


def _load_cost_index_multiplier(lake: Optional[DataLake], *, msa_id: Optional[str], as_of: Optional[str]) -> float:
    if lake is None:
        return 1.0
    df = _safe_read(lake, "cost_indices", as_of=as_of, filters={"msa_id": msa_id} if msa_id else None)
    if df.empty:
        return 1.0
    for col in ("multiplier", "value", "index_value"):
        if col in df.columns and pd.notnull(df[col]).any():
            try:
                return float(df[col].iloc[-1])
            except Exception:
                continue
    return 1.0


def _load_energy_rate_factor(lake: Optional[DataLake], *, msa_id: Optional[str], as_of: Optional[str]) -> float:
    """Return a proportional factor to scale annual_savings based on energy rates.

    If no data, return 1.0. If dataset provides an absolute rate (e.g., $/kWh),
    we approximate a factor by normalizing to its median across the partition.
    """
    if lake is None:
        return 1.0
    df = _safe_read(lake, "energy_rates", as_of=as_of, filters={"msa_id": msa_id} if msa_id else None)
    if df.empty:
        return 1.0
    series = None
    for col in ("rate", "usd_per_kwh", "value"):
        if col in df.columns and pd.notnull(df[col]).any():
            series = pd.to_numeric(df[col], errors="coerce")
            break
    if series is None or series.dropna().empty:
        return 1.0
    median = float(series.median()) if pd.notnull(series.median()) else 0.0
    last = float(series.iloc[-1]) if pd.notnull(series.iloc[-1]) else median
    return (last / median) if median > 0 else 1.0


def _load_downtime_rate(lake: Optional[DataLake], *, asset_category: Optional[str], as_of: Optional[str]) -> float:
    if lake is None:
        return 0.0
    filters: Dict[str, object] | None = {"asset_category": asset_category} if asset_category else None
    df = _safe_read(lake, "downtime_cost_rates", as_of=as_of, filters=filters)
    if df.empty:
        return 0.0
    for col in ("rate_per_hour", "usd_per_hour", "value"):
        if col in df.columns and pd.notnull(df[col]).any():
            try:
                return float(df[col].iloc[-1])
            except Exception:
                continue
    return 0.0


def _load_vendor_quote(lake: Optional[DataLake], *, asset_id: str, scope_name: str, as_of: Optional[str]) -> Optional[float]:
    if lake is None:
        return None
    df = _safe_read(
        lake,
        "vendor_quotes",
        as_of=as_of,
        filters={"asset_id": asset_id, "scope_name": scope_name},
    )
    if df.empty:
        return None
    for col in ("cost", "quoted_cost", "value"):
        if col in df.columns and pd.notnull(df[col]).any():
            try:
                return float(df[col].iloc[-1])
            except Exception:
                continue
    return None


def rank_scopes_with_etl(
    asset_id: str,
    scopes: Sequence[ScopeTemplate],
    *,
    config: Optional[RankConfig] = None,
    session: Optional[Session] = None,
    lake: Optional[DataLake] = None,
    as_of: Optional[str] = None,
    msa_id: Optional[str] = None,
    asset_category: Optional[str] = None,
) -> List[RankedScope]:
    """Adjust templates using ETL inputs (if available) then rank.

    Adjustments:
      - cost *= cost_index_multiplier
      - annual_savings *= energy_rate_factor
      - downtime_cost_rate_per_hour = downtime_rate (if provided)
      - vendor quote overrides cost when present
    Missing datasets are treated as neutral (no change).
    """
    resolved_msa = _resolve_msa_id(session, asset_id, msa_id)
    cost_index_mult = _load_cost_index_multiplier(lake, msa_id=resolved_msa, as_of=as_of)
    energy_rate_factor = _load_energy_rate_factor(lake, msa_id=resolved_msa, as_of=as_of)
    downtime_rate = _load_downtime_rate(lake, asset_category=asset_category, as_of=as_of)

    adjusted: List[ScopeTemplate] = []
    for s in scopes:
        quoted_cost = _load_vendor_quote(lake, asset_id=asset_id, scope_name=s.name, as_of=as_of)
        adjusted_cost = quoted_cost if quoted_cost is not None else float(s.cost) * cost_index_mult
        adjusted_savings = float(s.annual_savings) * energy_rate_factor
        adjusted_scope = replace(
            s,
            cost=adjusted_cost,
            annual_savings=adjusted_savings,
            downtime_cost_rate_per_hour=(
                float(s.downtime_cost_rate_per_hour)
                if s.downtime_cost_rate_per_hour > 0
                else float(downtime_rate)
            ),
        )
        adjusted.append(adjusted_scope)

    return rank_scopes(asset_id, adjusted, config=config)


