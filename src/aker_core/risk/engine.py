"""Risk engine implementation translating hazard ETL outputs into underwriting multipliers."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Mapping, MutableMapping, Optional, Sequence

from sqlalchemy.orm import Session

from aker_data.hazards import HazardDataStore, HazardRecord

from ..database.risk import RiskRepository
from .calibration import RiskCalibrator
from .types import RiskEntry

SUPPORTED_SUBJECT_TYPES = {"market", "asset"}


def _normalise_subject(subject: object) -> tuple[str, str]:
    """Resolve (subject_type, subject_id) from supported payload patterns."""

    if isinstance(subject, str):
        return "market", subject

    if isinstance(subject, Mapping):
        mapping: Mapping[str, object] = subject
        if "subject_type" in mapping and "subject_id" in mapping:
            return str(mapping["subject_type"]).lower(), str(mapping["subject_id"])
        if "msa_id" in mapping:
            return "market", str(mapping["msa_id"])
        if "asset_id" in mapping:
            return "asset", str(mapping["asset_id"])

    # Attribute-based fallbacks (simple dataclass/ORM objects)
    if hasattr(subject, "subject_type") and hasattr(subject, "subject_id"):
        return str(getattr(subject, "subject_type")).lower(), str(getattr(subject, "subject_id"))
    if hasattr(subject, "msa_id"):
        return "market", str(getattr(subject, "msa_id"))
    if hasattr(subject, "asset_id"):
        return "asset", str(getattr(subject, "asset_id"))

    raise ValueError(
        "Unsupported subject payload. Provide a market identifier string or a mapping/object "
        "with subject_type/subject_id, msa_id, or asset_id attributes."
    )


def _merge_deductible(entry_dict: dict[str, object], hazard_record: Optional[HazardRecord]) -> dict[str, object]:
    deductible = dict(entry_dict["deductible"])
    if hazard_record and hazard_record.metadata:
        # Include metadata keys that do not clobber the default deductible payload.
        for key, value in hazard_record.metadata.items():
            deductible.setdefault(key, value)
    return deductible


def compute(
    subject: object,
    peril: str,
    *,
    session: Optional[Session] = None,
    run_id: Optional[int] = None,
    hazard_store: Optional[HazardDataStore] = None,
    calibrator: Optional[RiskCalibrator] = None,
    default_data_vintage: Optional[str] = None,
    notes: Optional[str] = None,
) -> RiskEntry:
    """Compute the `RiskEntry` for the requested subject and peril."""

    store = hazard_store or HazardDataStore.instance()
    calibrator = calibrator or RiskCalibrator()
    subject_type, subject_id = _normalise_subject(subject)

    if subject_type not in SUPPORTED_SUBJECT_TYPES:
        raise ValueError(f"Unsupported subject_type '{subject_type}'. Expected one of {SUPPORTED_SUBJECT_TYPES}.")

    hazard_record = store.get(peril, subject_type, subject_id)
    severity_idx = hazard_record.severity_idx if hazard_record else 50.0
    data_vintage = (
        hazard_record.data_vintage
        if hazard_record and hazard_record.data_vintage
        else (default_data_vintage or date.today().strftime("%Y-%m"))
    )
    source = hazard_record.source if hazard_record else calibrator.source(peril)

    multiplier = calibrator.multiplier(peril, severity_idx)
    deductible = calibrator.deductible_guidance(peril, severity_idx)
    if notes is None and hazard_record and "note" in hazard_record.metadata:
        notes = str(hazard_record.metadata["note"])

    entry = RiskEntry(
        subject_type=subject_type,
        subject_id=subject_id,
        peril=peril.lower(),
        severity_idx=round(float(severity_idx), 4),
        multiplier=round(float(multiplier), 6),
        deductible=deductible,
        data_vintage=data_vintage,
        source=source,
        notes=notes,
    )

    if hazard_record:
        # Rebuild entry with merged deductible metadata while preserving dataclass immutability.
        entry_dict = entry.as_dict()
        entry_dict["deductible"] = _merge_deductible(entry_dict, hazard_record)
        entry = RiskEntry(**entry_dict)

    if session is not None:
        repository = RiskRepository(session)
        repository.upsert_profile(entry, run_id=run_id, calculation_method=calibrator.version)

    return entry


class RiskEngine:
    """Risk engine responsible for computing and applying risk adjustments."""

    def __init__(
        self,
        session: Session,
        *,
        hazard_store: Optional[HazardDataStore] = None,
        calibrator: Optional[RiskCalibrator] = None,
    ) -> None:
        self.session = session
        self.hazard_store = hazard_store or HazardDataStore.instance()
        self.calibrator = calibrator or RiskCalibrator()
        self.repository = RiskRepository(session)

    def compute(
        self,
        subject: object,
        peril: str,
        *,
        run_id: Optional[int] = None,
        default_data_vintage: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> RiskEntry:
        """Proxy to module-level `compute` using the engine configuration."""

        return compute(
            subject,
            peril,
            session=self.session,
            run_id=run_id,
            hazard_store=self.hazard_store,
            calibrator=self.calibrator,
            default_data_vintage=default_data_vintage,
            notes=notes,
        )

    def apply_to_underwrite(
        self,
        payload: Mapping[str, float | int | str],
        entries: Sequence[RiskEntry],
    ) -> dict[str, object]:
        """Apply risk multipliers to an underwriting payload."""

        if not entries:
            return dict(payload)

        adjusted: MutableMapping[str, object] = deepcopy(dict(payload))
        cumulative_multiplier = 1.0
        adjustments = []
        for entry in entries:
            cumulative_multiplier *= entry.multiplier
            adjustments.append({
                "peril": entry.peril,
                "multiplier": entry.multiplier,
                "severity_idx": entry.severity_idx,
                "data_vintage": entry.data_vintage,
                "source": entry.source,
            })

        exit_cap = adjusted.get("exit_cap_rate")
        if isinstance(exit_cap, (int, float)):
            adjusted["risk_adjusted_exit_cap_rate"] = round(float(exit_cap) * cumulative_multiplier, 6)

        contingency = adjusted.get("contingency_pct")
        if isinstance(contingency, (int, float)):
            adjusted["risk_adjusted_contingency_pct"] = round(float(contingency) * cumulative_multiplier, 6)

        adjusted["risk_multiplier"] = round(cumulative_multiplier, 6)
        adjusted["risk_adjustments"] = adjustments
        return dict(adjusted)

    def list_profile(self, subject: object) -> list[RiskEntry]:
        """Return stored risk profiles for the subject as `RiskEntry` objects."""

        subject_type, subject_id = _normalise_subject(subject)
        rows = self.repository.list_subject_profiles(subject_type, subject_id)
        results = []
        for row in rows:
            entry = RiskEntry(
                subject_type=row.subject_type,
                subject_id=row.subject_id,
                peril=row.peril,
                severity_idx=row.severity_idx,
                multiplier=row.multiplier,
                deductible=row.deductible or {},
                data_vintage=row.data_vintage or "unknown",
                source=row.source or "unknown",
                notes=row.notes,
            )
            results.append(entry)
        return results


__all__ = ["RiskEngine", "compute"]
