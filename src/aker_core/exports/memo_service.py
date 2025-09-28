"""Services that assemble memo contexts from persisted analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.models import (
    AssetFit,
    Lineage,
    MarketJobs,
    MarketOutdoors,
    MarketSupply,
    MarketUrban,
    Markets,
    OpsModel,
    PillarScores,
    RiskProfile,
    StateRules,
)

from .memo_context import MemoContextBuilder, MemoContextPayload

_DEFAULT_PERILS: Sequence[str] = ("wildfire", "hail", "flood")


@dataclass(slots=True)
class MemoContextService:
    """Facade that gathers memo inputs from domain repositories."""

    session: Optional[Session] = None
    builder: Optional[MemoContextBuilder] = None

    def __post_init__(self) -> None:
        if self.builder is None:
            self.builder = MemoContextBuilder(session=self.session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_context(
        self,
        *,
        msa_id: str,
        run_id: str,
        git_sha: str,
        created_at: datetime,
        images: Mapping[str, str] | None,
        as_of: Optional[date] = None,
        asset_id: Optional[int] = None,
        state_code: Optional[str] = None,
        risk_perils: Sequence[str] | None = None,
    ) -> MemoContextPayload:
        """Construct memo context using stored analytics with safe fallbacks."""

        market_meta = self._collect_market_meta(msa_id=msa_id, as_of=as_of)
        market_tables = self._collect_market_tables(msa_id=msa_id)
        risk = self._collect_risk(msa_id=msa_id, perils=risk_perils)
        asset = self._collect_asset(asset_id=asset_id)
        ops = self._collect_ops(asset_id=asset_id)
        state_pack = self._collect_state_pack(state_code=state_code or market_meta.get("state_code"))
        data_vintage = self._collect_data_vintage(run_id=run_id)

        payload = self.builder.build(
            msa=market_meta,
            market_tables=market_tables,
            risk=risk,
            data_vintage=data_vintage,
            run_id=run_id,
            git_sha=git_sha,
            created_at=created_at,
            images=images or {},
            asset=asset,
            ops=ops,
            state_pack=state_pack,
        )
        return payload

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------
    def _collect_market_meta(self, *, msa_id: str, as_of: Optional[date]) -> Dict[str, Any]:
        record_name = None
        state_code = None

        if self.session is not None:
            stmt = select(Markets.name).where(Markets.msa_id == msa_id)
            record_name = self.session.execute(stmt).scalar_one_or_none()
            # Attempt to infer state from the MSA code (e.g. "DEN-CO")
            if "-" in msa_id:
                state_code = msa_id.split("-")[-1]

        pillar_scores = None
        if self.session is not None:
            stmt = (
                select(PillarScores)
                .where(PillarScores.msa_id == msa_id)
                .order_by(PillarScores.score_as_of.desc().nullslast())
                .limit(1)
            )
            pillar_scores = self.session.execute(stmt).scalar_one_or_none()

        if pillar_scores is not None and as_of is None:
            as_of = pillar_scores.score_as_of or as_of

        as_of_str = (as_of or date.today()).isoformat()

        scores = {
            "supply_0_5": self._round(pillar_scores.supply_0_5 if pillar_scores else None, default=0.0),
            "jobs_0_5": self._round(pillar_scores.jobs_0_5 if pillar_scores else None, default=0.0),
            "urban_0_5": self._round(pillar_scores.urban_0_5 if pillar_scores else None, default=0.0),
            "outdoor_0_5": self._round(pillar_scores.outdoor_0_5 if pillar_scores else None, default=0.0),
            "weighted_0_5": self._round(pillar_scores.weighted_0_5 if pillar_scores else None, default=0.0),
            "weighted_0_100": self._round(
                pillar_scores.weighted_0_100 if pillar_scores else None,
                default=self._round(
                    (pillar_scores.weighted_0_5 or 0) * 20 if pillar_scores else 0.0
                ),
            ),
            "risk_multiplier": self._round(
                pillar_scores.risk_multiplier if pillar_scores else None,
                default=1.0,
            ),
        }

        return {
            "msa_id": msa_id,
            "name": record_name or msa_id,
            "as_of": as_of_str,
            "pillar_scores": scores,
            "state_code": state_code,
        }

    def _collect_market_tables(self, *, msa_id: str) -> Dict[str, list[dict[str, Any]]]:
        if self.session is None:
            return self._fallback_market_tables()

        tables: Dict[str, list[dict[str, Any]]] = {
            "supply": [],
            "jobs": [],
            "urban": [],
            "outdoors": [],
        }

        supply = self.session.execute(
            select(MarketSupply)
            .where(MarketSupply.msa_id == msa_id)
            .order_by(MarketSupply.v_intake.desc().nullslast())
            .limit(1)
        ).scalar_one_or_none()
        if supply is not None:
            tables["supply"] = self._build_metric_rows(
                supply,
                metrics=[
                    ("permit_per_1k", "Permits per 1k", "permits", self._normalise_generic),
                    ("vacancy_rate", "Vacancy Rate", "%", self._normalise_percentage),
                    ("tom_days", "Time on Market", "days", self._normalise_generic),
                    ("height_idx", "Height Flexibility", "idx", self._normalise_generic),
                ],
            )

        jobs = self.session.execute(
            select(MarketJobs)
            .where(MarketJobs.msa_id == msa_id)
            .order_by(MarketJobs.calculated_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if jobs is not None:
            tables["jobs"] = self._build_metric_rows(
                jobs,
                metrics=[
                    ("tech_lq", "Tech LQ", "idx", self._normalise_generic),
                    ("health_lq", "Health LQ", "idx", self._normalise_generic),
                    ("startup_density", "Startup Density", "idx", self._normalise_generic),
                    ("unemployment_rate", "Unemployment", "%", self._normalise_percentage),
                ],
            )

        urban = self.session.execute(
            select(MarketUrban)
            .where(MarketUrban.msa_id == msa_id)
            .order_by(MarketUrban.v_intake.desc().nullslast())
            .limit(1)
        ).scalar_one_or_none()
        if urban is not None:
            tables["urban"] = self._build_metric_rows(
                urban,
                metrics=[
                    ("walk_15_ct", "15-min Walk Amenities", "count", self._normalise_generic),
                    ("transit_ct", "Transit Stops", "count", self._normalise_generic),
                    ("daytime_pop_1mi", "Daytime Pop (1mi)", "residents", self._normalise_generic),
                    ("retail_vac", "Retail Vacancy", "%", self._normalise_percentage),
                ],
            )

        outdoors = self.session.execute(
            select(MarketOutdoors)
            .where(MarketOutdoors.msa_id == msa_id)
            .order_by(MarketOutdoors.v_intake.desc().nullslast())
            .limit(1)
        ).scalar_one_or_none()
        if outdoors is not None:
            tables["outdoors"] = self._build_metric_rows(
                outdoors,
                metrics=[
                    ("trail_mi_pc", "Trail Miles per Capita", "mi", self._normalise_generic),
                    ("public_land_30min_pct", "Public Land (30m)", "%", self._normalise_percentage),
                    ("smoke_days", "Smoke Days", "days", self._normalise_inverse),
                    ("min_trail_min", "Nearest Trail", "minutes", self._normalise_inverse),
                ],
            )

        if all(not rows for rows in tables.values()):
            return self._fallback_market_tables()
        return tables

    def _collect_risk(self, *, msa_id: str, perils: Sequence[str] | None) -> Dict[str, Any]:
        perils = tuple(perils or _DEFAULT_PERILS)
        multipliers: list[dict[str, Any]] = []

        if self.session is not None:
            stmt = select(RiskProfile).where(
                RiskProfile.subject_type == "market",
                RiskProfile.subject_id == msa_id,
                RiskProfile.peril.in_(perils),
            )
            records = list(self.session.execute(stmt).scalars())
            for record in records:
                multipliers.append(
                    {
                        "peril": record.peril,
                        "multiplier": self._round(record.multiplier, default=1.0),
                        "exit_cap_bps_delta": self._bps_delta(record.multiplier),
                        "contingency_pct_delta": self._pct_delta(record.multiplier),
                    }
                )

        if not multipliers:
            for peril in perils:
                multipliers.append(
                    {
                        "peril": peril,
                        "multiplier": 1.0,
                        "exit_cap_bps_delta": 0,
                        "contingency_pct_delta": 0.0,
                    }
                )

        return {
            "multipliers": multipliers,
            "exit_cap_bps_delta": sum(item["exit_cap_bps_delta"] for item in multipliers),
            "contingency_pct_delta": round(
                sum(item["contingency_pct_delta"] for item in multipliers), 4
            ),
        }

    def _collect_asset(self, *, asset_id: Optional[int]) -> Dict[str, Any]:
        if asset_id is None or self.session is None:
            return {}

        record = self.session.execute(
            select(AssetFit).where(AssetFit.asset_id == asset_id)
        ).scalar_one_or_none()
        if record is None:
            return {}

        flags_payload: Iterable[dict[str, Any]]
        if record.flags and isinstance(record.flags, Mapping):
            rows = record.flags.get("rows")
            if isinstance(rows, Iterable):
                flags_payload = [dict(row) for row in rows]
            else:
                flags_payload = []
        else:
            flags_payload = []

        flags = [
            {
                "severity": flag.get("severity", "info"),
                "code": flag.get("code", ""),
                "message": flag.get("message", ""),
                "observed": flag.get("observed") or flag.get("context_label") or "—",
                "target": flag.get("target") or flag.get("ruleset_version") or "—",
            }
            for flag in flags_payload
        ]

        return {
            "asset_id": record.asset_id,
            "msa_id": record.msa_id,
            "fit_score": self._round(record.fit_score, default="No asset context provided"),
            "flags": flags,
        }

    def _collect_ops(self, *, asset_id: Optional[int]) -> Dict[str, Any]:
        if asset_id is None or self.session is None:
            return {}

        record = self.session.execute(
            select(OpsModel).where(OpsModel.asset_id == asset_id)
        ).scalar_one_or_none()
        if record is None:
            return {}

        nps_series = []
        if record.nps is not None:
            nps_series.append({"period": "Current", "score": record.nps})

        reviews_series = []
        if record.reputation_idx is not None:
            reviews_series.append(
                f"Latest reputation index derived from reviews: {self._round(record.reputation_idx)}"
            )

        return {
            "reputation_idx": self._round(record.reputation_idx, default="No operations data available"),
            "nps_series": nps_series,
            "reviews_series": reviews_series,
        }

    def _collect_state_pack(self, *, state_code: Optional[str]) -> Dict[str, Any]:
        if state_code is None or self.session is None:
            return {}

        record = self.session.execute(
            select(StateRules)
            .where(StateRules.state_code == state_code.upper())
            .order_by(StateRules.applied_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if record is None:
            return {"code": state_code.upper()}

        changes: list[dict[str, Any]] = []
        snapshot = record.rule_snapshot or {}
        for section, payload in snapshot.items():
            if isinstance(payload, Mapping):
                current = payload.get("current") or payload.get("baseline") or "—"
                proposed = payload.get("proposed") or payload.get("target") or "—"
            else:
                current = "—"
                proposed = payload
            changes.append(
                {
                    "section": section,
                    "setting": payload.get("setting") if isinstance(payload, Mapping) else section,
                    "current": current,
                    "proposed": proposed,
                }
            )

        return {
            "code": state_code.upper(),
            "changes": changes,
        }

    def _collect_data_vintage(self, *, run_id: str) -> Dict[str, str]:
        if self.session is None:
            return {}

        try:
            run_id_int = int(run_id)
        except (TypeError, ValueError):
            return {}

        stmt = select(Lineage).where(Lineage.run_id == run_id_int)
        records = list(self.session.execute(stmt).scalars())
        if not records:
            return {}

        vintage: MutableMapping[str, str] = {}
        for record in records:
            if record.source:
                fetched = record.fetched_at.isoformat() if record.fetched_at else ""
                vintage[record.source] = fetched[:7] if fetched else ""
            else:
                vintage[record.table] = record.hash
        return dict(vintage)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _build_metric_rows(
        self,
        record: Any,
        *,
        metrics: Iterable[tuple[str, str, str, callable]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for attr, label, unit, normaliser in metrics:
            value = getattr(record, attr, None)
            if value is None:
                continue
            raw = self._round(value)
            normalized = normaliser(value)
            rows.append(
                {
                    "metric_label": label,
                    "value_raw": raw,
                    "unit": unit,
                    "normalized_0_100": normalized,
                }
            )
        return rows

    def _fallback_market_tables(self) -> Dict[str, list[dict[str, Any]]]:
        return {
            "supply": [
                {
                    "metric_label": "Permit Velocity",
                    "value_raw": 120,
                    "unit": "bps",
                    "normalized_0_100": 82,
                }
            ],
            "jobs": [
                {
                    "metric_label": "STEM Hiring",
                    "value_raw": 18,
                    "unit": "%",
                    "normalized_0_100": 88,
                }
            ],
            "urban": [
                {
                    "metric_label": "Transit Score",
                    "value_raw": 65,
                    "unit": "idx",
                    "normalized_0_100": 70,
                }
            ],
            "outdoors": [
                {
                    "metric_label": "Trail Access",
                    "value_raw": 42,
                    "unit": "idx",
                    "normalized_0_100": 77,
                }
            ],
        }

    @staticmethod
    def _round(value: Any, *, default: Any = 0.0, precision: int = 2) -> Any:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return round(float(value), precision)
        return value

    @staticmethod
    def _normalise_generic(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return round(max(0.0, min(100.0, numeric)), 2)

    @staticmethod
    def _normalise_percentage(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if numeric <= 1:
            numeric *= 100
        return round(max(0.0, min(100.0, numeric)), 2)

    @staticmethod
    def _normalise_inverse(value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if numeric <= 0:
            return 100.0
        score = max(0.0, 100.0 - numeric)
        return round(score, 2)

    @staticmethod
    def _bps_delta(multiplier: Optional[float]) -> int:
        if multiplier is None:
            return 0
        return int(round((float(multiplier) - 1.0) * 10000))

    @staticmethod
    def _pct_delta(multiplier: Optional[float]) -> float:
        if multiplier is None:
            return 0.0
        return round((float(multiplier) - 1.0) * 100, 4)


__all__ = ["MemoContextService"]
