"""Regulatory friction encoders."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, MutableMapping, Optional, Union

from .store import RegulatoryStore, get_store


RegulatoryInput = Union[str, Mapping[str, object]]
EncodingDict = Dict[str, Union[bool, int]]


KEYWORD_SETS = {
    "iz": {"inclusionary zoning", "affordable housing set-aside", "iz requirement"},
    "design_review": {"design review", "architectural review", "planning commission review"},
    "water": {"water moratorium", "water availability moratorium", "water connection pause"},
}


@dataclass
class RegulatoryEncoder:
    """High-level façade for regulatory friction encoding."""

    store: Optional[RegulatoryStore] = None

    def encode(
        self,
        source: RegulatoryInput,
        *,
        msa_id: Optional[str] = None,
        persist: bool = True,
    ) -> EncodingDict:
        """Encode regulatory signals and optionally persist the result."""

        encoding = encode_rules(source)
        if msa_id and persist:
            (self.store or get_store()).upsert(msa_id, encoding, provenance=encoding.get("provenance"))
        return encoding


def encode_rules(
    source: RegulatoryInput,
    *,
    msa_id: Optional[str] = None,
    persist: bool = True,
    store: Optional[RegulatoryStore] = None,
) -> EncodingDict:
    """Normalise regulatory signals into a scoring-ready payload.

    Parameters
    ----------
    source
        Either a narrative text string or a mapping with optional ``text`` and
        ``tables`` entries describing the municipal regulatory environment.
    msa_id
        Optional market identifier used when persisting results.
    persist
        Whether to push the resulting encoding into the shared regulatory store.
    store
        Optional explicit store instance to use for persistence.
    """

    text, tables = _normalise_input(source)
    provenance: Dict[str, str] = {}

    iz_flag = _detect_flag(
        text,
        tables,
        KEYWORD_SETS["iz"],
        tables_keys=("inclusionary", "iz_flag"),
        provenance=provenance,
        key="iz_flag",
        negations={"no inclusionary zoning", "without inclusionary zoning", "no iz"},
    )
    review_flag = _detect_flag(
        text,
        tables,
        KEYWORD_SETS["design_review"],
        tables_keys=("design_review", "review_required"),
        provenance=provenance,
        key="review_flag",
    )
    water_flag = _detect_flag(
        text,
        tables,
        KEYWORD_SETS["water"],
        tables_keys=("water_moratorium", "water_flag"),
        provenance=provenance,
        key="water_moratorium_flag",
        negations={
            "moratorium lifted",
            "no water moratorium",
            "moratorium expired",
        },
    )

    height_limit = _extract_numeric(text, tables, keys=("height_limit", "far_limit"))
    parking_min = _extract_numeric(text, tables, keys=("parking_min", "parking_ratio"))

    height_idx = _normalise_height(height_limit)
    parking_idx = _normalise_parking(parking_min)

    encoding: EncodingDict = {
        "iz_flag": iz_flag,
        "review_flag": review_flag,
        "height_idx": height_idx,
        "parking_idx": parking_idx,
        "water_moratorium_flag": water_flag,
        "provenance": provenance,
    }

    if msa_id and persist:
        (store or get_store()).upsert(msa_id, encoding, provenance=provenance)

    return encoding


def _normalise_input(source: RegulatoryInput) -> tuple[str, Mapping[str, object]]:
    if isinstance(source, str):
        return source, {}

    text = str(source.get("text", ""))
    tables = source.get("tables")
    if isinstance(tables, Mapping):
        return text, tables
    return text, {}


def _detect_flag(
    text: str,
    tables: Mapping[str, object],
    keywords: Iterable[str],
    *,
    tables_keys: Iterable[str],
    provenance: MutableMapping[str, str],
    key: str,
    negations: Optional[Iterable[str]] = None,
) -> bool:
    text_lower = text.lower()
    negation_hits = {phrase for phrase in (negations or []) if phrase in text_lower}
    if negation_hits:
        provenance[key] = f"negated by: {sorted(negation_hits)[0]}"
        return False

    for keyword in keywords:
        if keyword in text_lower:
            provenance[key] = f"matched text keyword: {keyword}"
            return True

    for table_key in tables_keys:
        value = tables.get(table_key)
        if isinstance(value, bool):
            provenance[key] = f"table flag {table_key}"
            return value
        if isinstance(value, str) and value.strip():
            lowered = value.strip().lower()
            if lowered in {"true", "yes", "y"}:
                provenance[key] = f"table flag {table_key}"
                return True
            if lowered in {"false", "no", "n"}:
                provenance[key] = f"table flag {table_key}"
                return False
    return False


def _extract_numeric(text: str, tables: Mapping[str, object], keys: Iterable[str]) -> Optional[float]:
    for key in keys:
        if key in tables:
            value = tables[key]
            try:
                return float(value)
            except (TypeError, ValueError):
                continue

    lowered = text.lower()
    for key in keys:
        pattern = rf"{key}\s*[:=]\s*(?P<num>\d+(?:\.\d+)?)"
        match = re.search(pattern, lowered)
        if match and match.group("num"):
            try:
                return float(match.group("num"))
            except ValueError:
                continue

    # Additional heuristic: look for explicit phrases like "height limit of 80 feet"
    generic_match = re.search(r"(height|far|parking)\D*(?P<num>\d+(?:\.\d+)?)", text.lower())
    if generic_match:
        try:
            return float(generic_match.group("num"))
        except ValueError:
            return None
    return None


def _normalise_height(height_limit: Optional[float]) -> int:
    if height_limit is None:
        return 0
    capped = max(0.0, min(height_limit, 200.0))
    score = int(round((200.0 - capped) / 200.0 * 100))
    return max(0, min(score, 100))


def _normalise_parking(parking_min: Optional[float]) -> int:
    if parking_min is None:
        return 0
    ratio = max(0.0, min(parking_min, 4.0))
    score = int(round((ratio / 4.0) * 100))
    return max(0, min(score, 100))
