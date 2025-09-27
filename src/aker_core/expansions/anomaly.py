"""Anomaly detection helpers for expansion events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import pandas as pd

from .models import ExpansionEvent


@dataclass
class AnomalyAssessment:
    jobs_zscore: Optional[float]
    investment_zscore: Optional[float]
    flags: List[str]


class AnomalyDetector:
    """Computes simple z-score anomalies from historical expansion data."""

    def __init__(
        self,
        historical_events: Optional[pd.DataFrame] = None,
        jobs_threshold: float = 3.0,
        investment_threshold: float = 3.0,
    ) -> None:
        self.jobs_threshold = jobs_threshold
        self.investment_threshold = investment_threshold
        self._baseline = (
            historical_events[
                [
                    "state",
                    "industry",
                    "jobs_created",
                    "investment_amount",
                ]
            ]
            if historical_events is not None and not historical_events.empty
            else None
        )

    def score(self, event: ExpansionEvent) -> AnomalyAssessment:
        if self._baseline is None:
            return AnomalyAssessment(jobs_zscore=None, investment_zscore=None, flags=[])

        subset = self._baseline
        if event.state:
            subset = subset[subset["state"].fillna("") == event.state]
        if event.industry:
            subset = subset[subset["industry"].fillna("") == event.industry]
        if subset.empty:
            subset = self._baseline

        flags: List[str] = []
        jobs_zscore = self._compute_zscore(subset["jobs_created"], event.jobs_created)
        investment_zscore = self._compute_zscore(
            subset["investment_amount"], event.investment_amount
        )

        if jobs_zscore is not None and abs(jobs_zscore) >= self.jobs_threshold:
            flags.append(f"jobs_zscore={jobs_zscore:.2f}")
        if investment_zscore is not None and abs(investment_zscore) >= self.investment_threshold:
            flags.append(f"investment_zscore={investment_zscore:.2f}")

        return AnomalyAssessment(
            jobs_zscore=jobs_zscore, investment_zscore=investment_zscore, flags=flags
        )

    @staticmethod
    def _compute_zscore(
        series: Iterable[Optional[float]], value: Optional[float]
    ) -> Optional[float]:
        data = pd.Series([x for x in series if x is not None])
        if value is None or data.empty:
            return None
        mean = data.mean()
        std = data.std(ddof=0)
        if std == 0:
            return None
        return (value - mean) / std


__all__ = ["AnomalyDetector", "AnomalyAssessment"]
