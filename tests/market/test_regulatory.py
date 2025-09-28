from __future__ import annotations

import json
from pathlib import Path

import pytest

from aker_market.regulatory import RegulatoryEncoder, encode_rules, get_store

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "regulatory_truths.json"


@pytest.fixture(autouse=True)
def clear_store():
    store = get_store()
    store.clear()
    yield
    store.clear()


def load_truths():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_encodings_match_truth_set():
    truths = load_truths()
    encoder = RegulatoryEncoder()

    for msa_id, payload in truths.items():
        result = encoder.encode(payload["input"], msa_id=msa_id)
        for key, expected_value in payload["expected"].items():
            assert result[key] == expected_value, f"Mismatch for {msa_id}::{key}"

    frame = get_store().to_frame()
    assert set(frame["msa_id"]) == set(truths.keys())


def test_encode_rules_defaults_when_signals_missing():
    result = encode_rules("Generic zoning update with no explicit rules")
    assert result["iz_flag"] is False
    assert result["review_flag"] is False
    assert result["height_idx"] == 0
    assert result["parking_idx"] == 0
    assert result["water_moratorium_flag"] is False


def test_encode_rules_accepts_structured_input():
    structured = {
        "text": "Design Review triggered downtown", 
        "tables": {"height_limit": 120, "parking_min": 1.5, "inclusionary": "yes"}
    }
    result = encode_rules(structured)
    assert result["iz_flag"] is True
    assert result["review_flag"] is True
    assert result["height_idx"] == 40
    assert result["parking_idx"] == 38


def test_store_records_provenance():
    encoder = RegulatoryEncoder()
    encoder.encode("Inclusionary zoning applies. HEIGHT_LIMIT=90", msa_id="test_msa")
    record = get_store().get("test_msa")
    assert record is not None
    provenance = json.loads(record["provenance"])
    assert "iz_flag" in provenance
    assert "height_idx" not in provenance  # only recorded when derived from text/table
