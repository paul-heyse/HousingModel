"""Services for maintaining pillar scores and triggering market composition."""

from __future__ import annotations

from datetime import date, datetime
from statistics import mean
from typing import Iterable, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.models import (
    MarketJobs,
    MarketOutdoors,
    Markets,
    MarketSupply,
    MarketUrban,
    PillarScores,
)

from .composer import MarketPillarScores, score


class PillarScoreService:
    """Derive pillar scores from domain tables and persist them for composition."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh_many(
        self,
        msa_ids: Optional[Sequence[str]] = None,
        *,
        as_of: date | datetime | str | None = None,
        run_id: Optional[int] = None,
        weights: Optional[dict[str, float]] = None,
    ) -> list[MarketPillarScores]:
        """Refresh pillar scores for multiple MSAs and compose markets when possible."""

        if msa_ids is None:
            msa_ids = [
                row[0] for row in self.session.execute(select(Markets.msa_id)).all() if row[0]
            ]

        metrics_by_msa = self._load_pillar_source_metrics(msa_ids)

        results: list[MarketPillarScores] = []
        for msa_id in msa_ids:
            result = self.refresh_one(
                msa_id,
                as_of=as_of,
                run_id=run_id,
                weights=weights,
                preloaded_metrics=metrics_by_msa.get(msa_id),
            )
            if result is not None:
                results.append(result)
        return results

    def refresh_one(
        self,
        msa_id: str,
        *,
        as_of: date | datetime | str | None = None,
        run_id: Optional[int] = None,
        weights: Optional[dict[str, float]] = None,
        preloaded_metrics: Optional[dict[str, object]] = None,
    ) -> Optional[MarketPillarScores]:
        """Refresh pillar scores for a single MSA and trigger composition if complete."""

        record = self._get_or_create(msa_id)

        metrics = preloaded_metrics or self._load_single_msa_metrics(msa_id)

        supply = self._compute_supply_score(metrics.get("supply"))
        jobs = self._compute_jobs_score(metrics.get("jobs"))
        urban = self._compute_urban_score(metrics.get("urban"))
        outdoor = self._compute_outdoor_score(metrics.get("outdoor"))

        updated = False
        if supply is not None:
            record.supply_0_5 = supply
            updated = True
        if jobs is not None:
            record.jobs_0_5 = jobs
            updated = True
        if urban is not None:
            record.urban_0_5 = urban
            updated = True
        if outdoor is not None:
            record.outdoor_0_5 = outdoor
            updated = True

        if updated and run_id is not None:
            record.run_id = run_id
        if updated and as_of is not None:
            record.score_as_of = self._coerce_date(as_of)

        self.session.flush()

        if self._has_all_pillars(record):
            return score(
                session=self.session,
                msa_id=msa_id,
                as_of=as_of,
                weights=weights,
                run_id=run_id,
            )
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_or_create(self, msa_id: str) -> PillarScores:
        record = (
            self.session.execute(select(PillarScores).where(PillarScores.msa_id == msa_id).limit(1))
            .scalars()
            .first()
        )
        if record is None:
            record = PillarScores(msa_id=msa_id)
            self.session.add(record)
            self.session.flush()
        return record

    def _load_single_msa_metrics(self, msa_id: str) -> dict[str, object]:
        metrics = self._load_pillar_source_metrics([msa_id])
        return metrics.get(msa_id, {})

    def _load_pillar_source_metrics(self, msa_ids: Sequence[str]) -> dict[str, dict[str, object]]:
        unique_ids = list(dict.fromkeys(msa_ids))
        if not unique_ids:
            return {}

        metrics: dict[str, dict[str, object]] = {msa: {} for msa in unique_ids}

        supply_rows = self.session.execute(
            select(MarketSupply).where(MarketSupply.msa_id.in_(unique_ids))
        ).scalars()
        for row in supply_rows:
            metrics.setdefault(row.msa_id, {})["supply"] = row

        job_rows = self.session.execute(
            select(MarketJobs).where(MarketJobs.msa_id.in_(unique_ids))
        ).scalars()
        for row in job_rows:
            metrics.setdefault(row.msa_id, {})["jobs"] = row

        urban_rows = self.session.execute(
            select(MarketUrban).where(MarketUrban.msa_id.in_(unique_ids))
        ).scalars()
        for row in urban_rows:
            metrics.setdefault(row.msa_id, {})["urban"] = row

        outdoor_rows = self.session.execute(
            select(MarketOutdoors).where(MarketOutdoors.msa_id.in_(unique_ids))
        ).scalars()
        for row in outdoor_rows:
            metrics.setdefault(row.msa_id, {})["outdoor"] = row

        return metrics

    @staticmethod
    def _coerce_date(value: date | datetime | str) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return datetime.strptime(value, "%Y-%m").date().replace(day=1)
        raise TypeError("Unsupported date value for score_as_of")

    @staticmethod
    def _favor_higher(value: Optional[float], baseline: float, ceiling: float) -> Optional[float]:
        """Normalise a metric where higher is better using spec-defined anchors."""

        if value is None:
            return None
        if value <= baseline:
            return 0.0
        if value >= ceiling:
            return 1.0
        return float((value - baseline) / (ceiling - baseline))

    @staticmethod
    def _favor_lower(value: Optional[float], best: float, worst: float) -> Optional[float]:
        """Normalise a metric where lower is better, keeping guardrails explicit."""

        if value is None:
            return None
        if value <= best:
            return 1.0
        if value >= worst:
            return 0.0
        # The linear falloff matches the governance-approved heuristics documented
        # in the market scoring knowledge base; reviewers rely on these anchors
        # when auditing pillar scores for reasonableness.
        return float(1.0 - ((value - best) / (worst - best)))

    @staticmethod
    def _mean(scores: Iterable[Optional[float]]) -> Optional[float]:
        filtered = [score for score in scores if score is not None]
        if not filtered:
            return None
        return float(mean(filtered))

    @staticmethod
    def _to_0_5(score_fraction: Optional[float]) -> Optional[float]:
        if score_fraction is None:
            return None
        return float(max(0.0, min(score_fraction, 1.0)) * 5.0)

    @staticmethod
    def _has_all_pillars(record: PillarScores) -> bool:
        return all(
            getattr(record, field) is not None
            for field in ("supply_0_5", "jobs_0_5", "urban_0_5", "outdoor_0_5")
        )

    def _compute_supply_score(self, record: Optional[MarketSupply]) -> Optional[float]:
        if record is None:
            return None

        scores = [
            self._favor_lower(record.permit_per_1k, best=1.5, worst=10.0),
            self._favor_lower(record.vacancy_rate, best=3.0, worst=12.0),
            self._favor_lower(record.tom_days, best=20.0, worst=90.0),
            self._favor_lower(record.slope_pct, best=5.0, worst=35.0),
            self._favor_lower(record.buffer_pct, best=5.0, worst=40.0),
            self._favor_higher(record.height_idx, baseline=1.5, ceiling=4.0),
            self._favor_lower(record.parking_idx, best=0.0, worst=2.5),
        ]

        return self._to_0_5(self._mean(scores))

    def _compute_jobs_score(self, record: Optional[MarketJobs]) -> Optional[float]:
        if record is None:
            return None

        scores = [
            self._favor_higher(record.tech_lq, baseline=1.0, ceiling=2.0),
            self._favor_higher(record.health_lq, baseline=1.0, ceiling=2.0),
            self._favor_higher(record.education_lq, baseline=1.0, ceiling=2.0),
            self._favor_higher(record.manufacturing_lq, baseline=1.0, ceiling=2.0),
            self._favor_higher(record.defense_lq, baseline=1.0, ceiling=2.0),
            self._favor_higher(record.biotech_lq, baseline=1.0, ceiling=2.0),
            self._favor_higher(record.tech_cagr_5yr, baseline=0.0, ceiling=6.0),
            self._favor_higher(record.health_cagr_5yr, baseline=0.0, ceiling=5.0),
            self._favor_higher(record.education_cagr_5yr, baseline=0.0, ceiling=4.0),
            self._favor_higher(record.manufacturing_cagr_5yr, baseline=-1.0, ceiling=4.0),
            self._favor_higher(record.total_awards_per_100k, baseline=0.0, ceiling=300.0),
            self._favor_higher(record.bfs_applications_per_100k, baseline=0.0, ceiling=150.0),
            self._favor_higher(record.bfs_high_propensity_per_100k, baseline=0.0, ceiling=120.0),
            self._favor_higher(record.startup_density, baseline=0.0, ceiling=80.0),
            self._favor_higher(record.mig_25_44_per_1k, baseline=0.0, ceiling=25.0),
            self._favor_higher(record.expansions_total_ct, baseline=0.0, ceiling=50.0),
            self._favor_higher(record.expansions_total_jobs, baseline=0.0, ceiling=5000.0),
            self._favor_lower(record.unemployment_rate, best=2.5, worst=8.0),
            self._favor_higher(record.labor_participation_rate, baseline=55.0, ceiling=70.0),
        ]

        return self._to_0_5(self._mean(scores))

    def _compute_urban_score(self, record: Optional[MarketUrban]) -> Optional[float]:
        if record is None:
            return None

        scores = [
            self._favor_higher(record.walk_15_ct, baseline=10.0, ceiling=60.0),
            self._favor_higher(record.bike_15_ct, baseline=10.0, ceiling=60.0),
            self._favor_higher(record.k8_ct, baseline=5.0, ceiling=30.0),
            self._favor_higher(record.transit_ct, baseline=5.0, ceiling=40.0),
            self._favor_higher(record.urgent_ct, baseline=2.0, ceiling=15.0),
            self._favor_higher(record.interx_km2, baseline=30.0, ceiling=120.0),
            self._favor_higher(record.bikeway_conn_idx, baseline=20.0, ceiling=90.0),
            self._favor_lower(record.retail_vac, best=4.0, worst=18.0),
            self._favor_higher(record.retail_rent_qoq, baseline=0.0, ceiling=5.0),
            self._favor_higher(record.daytime_pop_1mi, baseline=50_000.0, ceiling=250_000.0),
            (1.0 if record.lastmile_flag else 0.0) if record.lastmile_flag is not None else None,
        ]

        return self._to_0_5(self._mean(scores))

    def _compute_outdoor_score(self, record: Optional[MarketOutdoors]) -> Optional[float]:
        if record is None:
            return None

        scores = [
            self._favor_lower(record.min_trail_min, best=15.0, worst=120.0),
            self._favor_lower(record.min_ski_bus_min, best=30.0, worst=180.0),
            self._favor_lower(record.min_water_min, best=20.0, worst=120.0),
            self._favor_lower(record.park_min, best=10.0, worst=90.0),
            self._favor_higher(record.trail_mi_pc, baseline=0.5, ceiling=4.0),
            self._favor_higher(record.public_land_30min_pct, baseline=30.0, ceiling=80.0),
            self._favor_lower(record.pm25_var, best=3.0, worst=10.0),
            self._favor_lower(record.smoke_days, best=0.0, worst=20.0),
            self._favor_higher(record.hw_rail_prox_idx, baseline=30.0, ceiling=100.0),
        ]

        return self._to_0_5(self._mean(scores))


__all__ = ["PillarScoreService"]
