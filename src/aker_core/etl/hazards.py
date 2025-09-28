"""ETL pipelines for hazard datasets feeding the risk engine."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Callable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

from aker_data.hazards import HazardDataStore, HazardRecord

from ..risk.calibration import DEFAULT_PERIL_CALIBRATIONS

logger = logging.getLogger(__name__)

Subject = Tuple[str, str]


def _normalise_subjects(subjects: Optional[Sequence[object]]) -> List[Subject]:
    if not subjects:
        return [("market", "MSA001"), ("market", "MSA002"), ("market", "MSA003")]

    normalised: List[Subject] = []
    for subject in subjects:
        if isinstance(subject, tuple) and len(subject) == 2:
            subject_type, subject_id = subject
        elif isinstance(subject, str):
            subject_type, subject_id = "market", subject
        elif isinstance(subject, Mapping):
            mapping = subject
            subject_type = str(mapping.get("subject_type", mapping.get("type", "market")))
            if "subject_id" in mapping:
                subject_id = str(mapping["subject_id"])
            elif "msa_id" in mapping:
                subject_id = str(mapping["msa_id"])
                subject_type = "market"
            elif "asset_id" in mapping:
                subject_id = str(mapping["asset_id"])
                subject_type = "asset"
            else:
                raise ValueError("Subject mapping must include subject_id, msa_id, or asset_id")
        else:
            raise ValueError(
                "Subjects must be strings, (subject_type, subject_id) tuples, or mappings with subject metadata"
            )
        normalised.append((subject_type.lower(), subject_id))
    return normalised


def _synthetic_severity(seed: str, *, minimum: float = 5.0, maximum: float = 95.0) -> float:
    """Deterministic severity generator based on a string seed."""

    value = abs(hash(seed)) % 10_000
    ratio = value / 10_000.0
    severity = minimum + (maximum - minimum) * ratio
    return round(severity, 2)


def _ingest_peril(
    peril: str,
    subjects: Sequence[Subject],
    *,
    data_vintage: str,
    hazard_store: HazardDataStore,
    metadata_factory: Optional[Mapping[str, object] | Callable[[str, str], Mapping[str, object]]] = None,
) -> List[HazardRecord]:
    calibrations = DEFAULT_PERIL_CALIBRATIONS.get(peril.lower())
    source = calibrations.source if calibrations else peril.title()
    records: List[HazardRecord] = []
    for subject_type, subject_id in subjects:
        severity = _synthetic_severity(f"{peril}:{subject_type}:{subject_id}")
        metadata: Mapping[str, object]
        if callable(metadata_factory):
            metadata = metadata_factory(subject_type, subject_id)
        elif isinstance(metadata_factory, Mapping):
            metadata = metadata_factory
        else:
            metadata = {}
        record = HazardRecord(
            subject_type=subject_type,
            subject_id=subject_id,
            severity_idx=severity,
            data_vintage=data_vintage,
            source=source,
            metadata=metadata,
        )
        records.append(record)
    hazard_store.ingest(peril, records)
    return records


def _records_to_frame(peril: str, records: Sequence[HazardRecord]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "peril": peril,
                "subject_type": record.subject_type,
                "subject_id": record.subject_id,
                "severity_idx": record.severity_idx,
                "data_vintage": record.data_vintage,
                "source": record.source,
                "metadata": dict(record.metadata),
            }
            for record in records
        ]
    )


def load_wildfire_wui(
    *,
    subjects: Optional[Sequence[object]] = None,
    as_of: Optional[str] = None,
    hazard_store: Optional[HazardDataStore] = None,
) -> pd.DataFrame:
    """Ingest Wildland-Urban Interface metrics and return the processed frame."""

    store = hazard_store or HazardDataStore.instance()
    subject_list = _normalise_subjects(subjects)
    data_vintage = as_of or datetime.now(UTC).strftime("%Y-%m")
    logger.info("Loading wildfire WUI hazard metrics for %s subjects", len(subject_list))
    records = _ingest_peril(
        "wildfire",
        subject_list,
        data_vintage=data_vintage,
        hazard_store=store,
        metadata_factory={"note": "Derived from synthetic WUI overlay"},
    )
    return _records_to_frame("wildfire", records)


def load_hail_frequency(
    *,
    subjects: Optional[Sequence[object]] = None,
    as_of: Optional[str] = None,
    hazard_store: Optional[HazardDataStore] = None,
) -> pd.DataFrame:
    """Ingest hail frequency metrics and return processed records."""

    store = hazard_store or HazardDataStore.instance()
    subject_list = _normalise_subjects(subjects)
    data_vintage = as_of or datetime.now(UTC).strftime("%Y-%m")
    logger.info("Loading hail hazard metrics for %s subjects", len(subject_list))
    records = _ingest_peril(
        "hail",
        subject_list,
        data_vintage=data_vintage,
        hazard_store=store,
        metadata_factory=lambda *_: {"deductible_floor_bps": 150.0},
    )
    return _records_to_frame("hail", records)


def load_snow_load(
    *,
    subjects: Optional[Sequence[object]] = None,
    as_of: Optional[str] = None,
    hazard_store: Optional[HazardDataStore] = None,
) -> pd.DataFrame:
    """Ingest snow load metrics for structural risk."""

    store = hazard_store or HazardDataStore.instance()
    subject_list = _normalise_subjects(subjects)
    data_vintage = as_of or datetime.now(UTC).strftime("%Y-%m")
    logger.info("Loading snow load hazard metrics for %s subjects", len(subject_list))
    records = _ingest_peril(
        "snow_load",
        subject_list,
        data_vintage=data_vintage,
        hazard_store=store,
        metadata_factory=lambda *_: {"structural_category": "ASCE7"},
    )
    return _records_to_frame("snow_load", records)


def load_water_stress(
    *,
    subjects: Optional[Sequence[object]] = None,
    as_of: Optional[str] = None,
    hazard_store: Optional[HazardDataStore] = None,
) -> pd.DataFrame:
    """Ingest water stress metrics combining aqueduct and drought severity."""

    store = hazard_store or HazardDataStore.instance()
    subject_list = _normalise_subjects(subjects)
    data_vintage = as_of or datetime.now(UTC).strftime("%Y-%m")
    logger.info("Loading water stress metrics for %s subjects", len(subject_list))
    records = _ingest_peril(
        "water_stress",
        subject_list,
        data_vintage=data_vintage,
        hazard_store=store,
        metadata_factory=lambda subject_type, subject_id: {
            "drought_category": "D2" if hash(subject_id) % 3 == 0 else "D1",
            "tap_moratorium_flag": bool(hash(subject_id) % 5 == 0),
        },
    )
    return _records_to_frame("water_stress", records)


def load_policy_risk(
    *,
    subjects: Optional[Sequence[object]] = None,
    as_of: Optional[str] = None,
    hazard_store: Optional[HazardDataStore] = None,
) -> pd.DataFrame:
    """Ingest policy and regulatory friction metrics."""

    store = hazard_store or HazardDataStore.instance()
    subject_list = _normalise_subjects(subjects)
    data_vintage = as_of or datetime.now(UTC).strftime("%Y-%m")
    logger.info("Loading policy risk metrics for %s subjects", len(subject_list))
    records = _ingest_peril(
        "policy_risk",
        subject_list,
        data_vintage=data_vintage,
        hazard_store=store,
        metadata_factory=lambda subject_type, subject_id: {
            "rent_control": bool(hash((subject_type, subject_id)) % 4 == 0),
            "insurance_regime": "strict" if hash(subject_id) % 2 == 0 else "baseline",
        },
    )
    return _records_to_frame("policy_risk", records)


__all__ = [
    "load_wildfire_wui",
    "load_hail_frequency",
    "load_snow_load",
    "load_water_stress",
    "load_policy_risk",
]
