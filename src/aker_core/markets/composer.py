"""Market pillar score composer.

This module coordinates the final weighting pass that turns the four market
pillars—supply, jobs, urban, outdoors—into a composite score suitable for both
0–5 and 0–100 representations. It also captures the weight profile used so the
result remains auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Mapping, MutableMapping, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.models import PillarScores

try:  # pragma: no cover - optional dependency for runtime detection
    from unittest.mock import Mock as _MockType
except Exception:  # pragma: no cover - environments without unittest
    _MockType = tuple()

_PILLAR_KEYS = ("supply", "jobs", "urban", "outdoor")
_DEFAULT_WEIGHTS: Mapping[str, float] = {
    "supply": 0.3,
    "jobs": 0.3,
    "urban": 0.2,
    "outdoor": 0.2,
}


@dataclass(frozen=True)
class MarketPillarScores:
    """Return payload describing the composed market scores."""

    msa_id: str
    supply_0_5: float
    jobs_0_5: float
    urban_0_5: float
    outdoor_0_5: float
    weighted_0_5: float
    weighted_0_100: float
    weights: Mapping[str, float]
    score_as_of: Optional[date]
    run_id: Optional[int]

    def to_dict(self) -> dict[str, float | str | int | None]:
        """Export the score payload as a dictionary for downstream consumers."""

        payload: dict[str, float | str | int | None] = {
            "msa_id": self.msa_id,
            "supply_0_5": self.supply_0_5,
            "jobs_0_5": self.jobs_0_5,
            "urban_0_5": self.urban_0_5,
            "outdoor_0_5": self.outdoor_0_5,
            "weighted_0_5": self.weighted_0_5,
            "weighted_0_100": self.weighted_0_100,
            "run_id": self.run_id,
            "score_as_of": self.score_as_of.isoformat() if self.score_as_of else None,
        }
        payload.update({f"weight_{key}": value for key, value in self.weights.items()})
        return payload


def _normalise_weights(overrides: Optional[Mapping[str, float]]) -> Mapping[str, float]:
    if not overrides:
        return _DEFAULT_WEIGHTS

    filtered: MutableMapping[str, float] = {
        key: float(overrides.get(key, 0.0)) for key in _PILLAR_KEYS
    }
    if any(value < 0 for value in filtered.values()):
        raise ValueError("Pillar weights must be non-negative")
    total = sum(filtered.values())
    if total <= 0:
        raise ValueError("At least one pillar weight must be greater than zero")
    return {key: value / total for key, value in filtered.items()}


def _as_date(value: date | datetime | str | None) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        # Accept YYYY-MM-DD or YYYY-MM strings
        for fmt, normaliser in (
            ("%Y-%m-%d", lambda dt: dt.date()),
            ("%Y-%m", lambda dt: dt.date().replace(day=1)),
        ):
            try:
                parsed = datetime.strptime(value, fmt)
                return normaliser(parsed)
            except ValueError:
                continue
        raise TypeError("score_as_of must be a date, datetime, ISO string, or None")
    raise TypeError("score_as_of must be a date, datetime, ISO string, or None")


def score(
    *,
    session: Session,
    msa_id: Optional[str] = None,
    msa_geo: Optional[str] = None,
    as_of: date | datetime | str | None = None,
    weights: Optional[Mapping[str, float]] = None,
    run_id: Optional[int] = None,
) -> MarketPillarScores:
    """Compose a deterministic market score for the provided market.

    Parameters
    ----------
    session
        Active SQLAlchemy session used to read and persist pillar scores.
    msa_id / msa_geo
        Identifier for the market whose pillar scores should be combined. The
        current implementation requires ``msa_id``; ``msa_geo`` is reserved for
        future geometry-based lookups and will raise if supplied without
        ``msa_id``.
    as_of
        Optional effective date for the composition. Accepts ``date`` or
        ``datetime`` instances as well as ``YYYY-MM``/``YYYY-MM-DD`` strings.
    weights
        Optional overrides for the default 0.3/0.3/0.2/0.2 weighting scheme. The
        mapping is normalised to sum to 1.0.
    run_id
        Optional run identifier that is persisted for lineage.
    """

    if session is None:
        raise ValueError("An active SQLAlchemy session is required")

    if msa_id is None:
        if msa_geo is not None:
            raise ValueError("msa_geo lookups require a resolved msa_id")
        raise ValueError("msa_id is required for market score composition")

    stmt = (
        select(PillarScores)
        .where(PillarScores.msa_id == msa_id)
        .order_by(PillarScores.id.desc())
        .limit(1)
    )
    record = session.execute(stmt).scalars().first()
    if record is None:
        raise ValueError(f"No pillar scores available for MSA '{msa_id}'")

    pillar_values = {
        "supply": record.supply_0_5,
        "jobs": record.jobs_0_5,
        "urban": record.urban_0_5,
        "outdoor": record.outdoor_0_5,
    }
    missing = [key for key, value in pillar_values.items() if value is None]
    if missing:
        raise ValueError(f"Missing pillar scores for {msa_id}: {', '.join(sorted(missing))}")

    weight_profile = dict(_normalise_weights(weights))

    composite_0_5 = sum(float(pillar_values[key]) * weight_profile[key] for key in _PILLAR_KEYS)

    # Deterministic composition without offsets for tests and production

    composite_0_100 = composite_0_5 * 20.0

    score_as_of = _as_date(as_of)

    record.weighted_0_5 = composite_0_5
    record.weighted_0_100 = composite_0_100
    record.weights = weight_profile
    record.score_as_of = score_as_of
    if run_id is not None:
        record.run_id = run_id

    session.flush()

    return MarketPillarScores(
        msa_id=msa_id,
        supply_0_5=float(pillar_values["supply"]),
        jobs_0_5=float(pillar_values["jobs"]),
        urban_0_5=float(pillar_values["urban"]),
        outdoor_0_5=float(pillar_values["outdoor"]),
        weighted_0_5=composite_0_5,
        weighted_0_100=composite_0_100,
        weights=weight_profile,
        score_as_of=score_as_of,
        run_id=run_id if run_id is not None else record.run_id,
    )


def score_many(
    *,
    session: Session,
    msa_ids: Optional[Sequence[str]] = None,
    as_of: date | datetime | str | None = None,
    weights: Optional[Mapping[str, float]] = None,
    run_id: Optional[int] = None,
) -> list[MarketPillarScores]:
    """Compose scores for multiple markets in a single call.

    Args:
        session: Active SQLAlchemy session used for persistence.
        msa_ids: Optional iterable of market identifiers. If omitted, all
            distinct MSAs present in ``pillar_scores`` are composed.
        as_of: Effective date applied to all compositions.
        weights: Optional weight overrides applied uniformly.
        run_id: Optional run identifier persisted with each composition.

    Returns:
        List of :class:`MarketPillarScores` results in the order processed.
    """

    if session is None:
        raise ValueError("An active SQLAlchemy session is required")

    if msa_ids is None:
        msa_ids = list(
            session.execute(
                select(PillarScores.msa_id).distinct().where(PillarScores.msa_id.is_not(None))
            )
        )
        msa_ids = [row[0] for row in msa_ids if row[0]]

    results: list[MarketPillarScores] = []
    for msa in msa_ids:
        results.append(
            score(
                session=session,
                msa_id=msa,
                as_of=as_of,
                weights=weights,
                run_id=run_id,
            )
        )
    return results


__all__ = ["MarketPillarScores", "score", "score_many"]
