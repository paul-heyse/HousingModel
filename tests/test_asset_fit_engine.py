from __future__ import annotations

from aker_core import AssetFitResult, asset_fit


def test_basic_fit_ok():
    asset = {
        "product_type": "garden",
        "year_built": 2015,
        "unit_mix": [{"type": "1BR", "pct": 0.6, "size_sqft": 700}],
        "ceiling_min_ft": 9.0,
        "wd_in_unit": True,
        "parking_ratio": 1.3,
    }
    context = {
        "label": "suburban",
        "allowed_product_types": ["garden", "midrise"],
        "min_year_built": 1980,
        "min_unit_size": {"1BR": 650},
        "min_ceiling_ft": 8.5,
        "require_wd_in_unit": True,
        "parking_ratio_required": 1.0,
    }
    res: AssetFitResult = asset_fit(asset=asset, context=context)
    assert res.fit_score == 100
    assert res.flags == []


def test_flags_and_scoring():
    asset = {
        "product_type": "midrise",
        "year_built": 1960,
        "unit_mix": [{"type": "1BR", "pct": 1.0, "size_sqft": 500}],
        "ceiling_min_ft": 8.0,
        "wd_in_unit": False,
        "parking_ratio": 0.8,
    }
    context = {
        "label": "urban",
        "allowed_product_types": ["garden"],
        "min_year_built": 1980,
        "min_unit_size": {"1BR": 650},
        "min_ceiling_ft": 8.5,
        "require_wd_in_unit": True,
        "parking_ratio_required": 1.0,
    }
    res = asset_fit(asset=asset, context=context)
    # Expect multiple deductions: type(25), vintage(10), size(5), ceiling(5), wd(15), parking(10) => 70
    assert res.fit_score == 30
    codes = {f["code"] for f in res.flags}
    assert {
        "PRODUCT_TYPE_DISALLOWED",
        "VINTAGE_BELOW_MIN",
        "UNIT_SIZE_UNDERSPEC",
        "CEILING_BELOW_MIN",
        "WASHER_DRYER_REQUIRED",
        "PARKING_SHORTFALL",
    }.issubset(codes)


def test_deterministic():
    asset = {
        "product_type": "garden",
        "year_built": 2000,
        "unit_mix": [{"type": "1BR", "pct": 1.0, "size_sqft": 700}],
        "ceiling_min_ft": 9.0,
        "wd_in_unit": True,
        "parking_ratio": 1.1,
    }
    context = {
        "label": "suburban",
        "allowed_product_types": ["garden"],
        "min_year_built": 1980,
        "min_unit_size": {"1BR": 650},
        "min_ceiling_ft": 8.5,
        "require_wd_in_unit": True,
        "parking_ratio_required": 1.0,
    }
    assert asset_fit(asset=asset, context=context).fit_score == asset_fit(asset=asset, context=context).fit_score
