from __future__ import annotations

from datetime import datetime, timezone

from aker_core.exports import MemoContextService


def test_memo_service_builds_payload_without_session(image_payload):
    service = MemoContextService(session=None)
    payload = service.build_context(
        msa_id="BOI",
        run_id="123",
        git_sha="abc1234",
        created_at=datetime(2024, 10, 5, 12, 30, 0),
        images=image_payload,
    )

    data = payload.data
    assert data["msa"]["msa_id"] == "BOI"
    assert data["market_tables"]["supply"]
    assert isinstance(payload.metadata.get("redactions"), int)


def test_memo_service_asset_fallback(image_payload):
    service = MemoContextService(session=None)
    payload = service.build_context(
        msa_id="DEN",
        run_id="456",
        git_sha="def5678",
        created_at=datetime.now(timezone.utc),
        images=image_payload,
        asset_id=None,
    )

    asset_section = payload.data.get("asset", {})
    assert asset_section.get("fit_score") == "No asset context provided"
