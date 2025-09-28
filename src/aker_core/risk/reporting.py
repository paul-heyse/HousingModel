"""Helpers for presenting risk entries in analyst-facing reports."""

from __future__ import annotations

from typing import Iterable, List

from .types import RiskEntry


def build_risk_table(entries: Iterable[RiskEntry]) -> List[dict[str, object]]:
    """Return a tabular representation suitable for exports and dashboards."""

    table: List[dict[str, object]] = []
    for entry in entries:
        row = {
            "Peril": entry.peril.replace("_", " ").title(),
            "SeverityIdx": entry.severity_idx,
            "Multiplier": entry.multiplier,
            "DataVintage": entry.data_vintage,
            "Source": entry.source,
            "RecommendedDeductibleBps": entry.deductible.get("recommended_deductible_bps"),
        }
        if entry.notes:
            row["Notes"] = entry.notes
        table.append(row)
    return table


__all__ = ["build_risk_table"]
