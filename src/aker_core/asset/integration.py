from __future__ import annotations

from typing import Mapping

from sqlalchemy.orm import Session

from aker_core.asset import fit
from aker_core.connectors.asset_data import (
    AssetAttributesConnector,
    ContextConnector,
    MarketCompsConnector,
    RegulatoryRulesConnector,
)
from aker_core.database.asset import AssetFitRepository


def evaluate_and_persist(
    *,
    session: Session,
    asset_connector: AssetAttributesConnector,
    context_connector: ContextConnector,
    rules_connector: RegulatoryRulesConnector | None = None,
    comps_connector: MarketCompsConnector | None = None,
    asset_id: int,
    asset_point: object | None = None,
    run_id: int | None = None,
) -> int:
    attrs = asset_connector.fetch(asset_id=asset_id)
    context = context_connector.infer(msa_id=attrs.msa_id, asset_point=asset_point)

    asset_payload: Mapping[str, object] = {
        "product_type": attrs.product_type,
        "year_built": attrs.year_built,
        "unit_mix": attrs.unit_mix,
        "ceiling_min_ft": attrs.ceiling_min_ft,
        "wd_in_unit": attrs.wd_in_unit,
        "parking_ratio": attrs.parking_ratio,
    }
    context_payload: Mapping[str, object] = {
        "label": context.label,
        "allowed_product_types": list(context.allowed_product_types),
        "min_year_built": context.min_year_built,
        "min_unit_size": dict(context.min_unit_size),
        "min_ceiling_ft": context.min_ceiling_ft,
        "require_wd_in_unit": context.require_wd_in_unit,
        "parking_ratio_required": context.parking_ratio_required,
    }

    result = fit(asset=asset_payload, context=context_payload)

    repo = AssetFitRepository(session)
    record = repo.create(
        asset_id=attrs.asset_id,
        msa_id=attrs.msa_id,
        product_type=attrs.product_type,
        fit_score=result.fit_score,
        flags={"rows": result.to_scenario_rows()},
        inputs=result.inputs,
        ruleset_version=result.ruleset_version,
        context_label=result.context_label,
        run_id=run_id,
    )
    session.commit()
    return int(record.asset_id)
