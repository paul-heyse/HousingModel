from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import pandas as pd

from .engine import fit


def _load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Asset Fit CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run asset fit on provided JSON payloads")
    run_p.add_argument("asset_json", help="Path to asset JSON payload")
    run_p.add_argument("context_json", help="Path to context JSON payload")
    run_p.add_argument("--export", choices=["csv", "json"], default="csv")
    run_p.add_argument("--out", type=str, default="asset_fit_scenarios.csv")

    gen_p = sub.add_parser("generate-scenario", help="Generate sample scenarios and export")
    gen_p.add_argument("--n", type=int, default=5, help="Number of scenarios to generate")
    gen_p.add_argument("--export", choices=["csv", "json"], default="csv")
    gen_p.add_argument("--out", type=str, default="asset_fit_sample_scenarios.csv")

    args = parser.parse_args(argv)

    if args.cmd == "run":
        asset = _load_json(args.asset_json)
        context = _load_json(args.context_json)
        result = fit(asset=asset, context=context)
        rows = result.to_scenario_rows()
        if args.export == "json":
            Path(args.out).write_text(json.dumps(rows, indent=2), encoding="utf-8")
        else:
            pd.DataFrame(rows).to_csv(args.out, index=False)
        summary_path = Path(args.out).with_suffix(".summary.json")
        summary_path.write_text(json.dumps({"fit_score": result.fit_score}, indent=2), encoding="utf-8")
        return 0

    if args.cmd == "generate-scenario":
        scenarios: list[dict[str, Any]] = []
        for _ in range(int(args.n)):
            asset = {
                "product_type": random.choice(["garden", "midrise", "highrise"]),
                "year_built": random.choice([1960, 1985, 2005, 2018]),
                "unit_mix": [
                    {"type": "1BR", "pct": 0.6, "size_sqft": random.choice([500, 650, 700])}
                ],
                "ceiling_min_ft": random.choice([8.0, 8.5, 9.0, 10.0]),
                "wd_in_unit": random.choice([True, False]),
                "parking_ratio": random.choice([0.8, 1.0, 1.2, 1.5]),
            }
            context = {
                "label": random.choice(["urban", "suburban", "transit-rich"]),
                "allowed_product_types": ["garden", "midrise"],
                "min_year_built": 1980,
                "min_unit_size": {"1BR": 650},
                "min_ceiling_ft": 8.5,
                "require_wd_in_unit": True,
                "parking_ratio_required": 1.0,
            }
            result = fit(asset=asset, context=context)
            for row in result.to_scenario_rows():
                scenarios.append({**row, "fit_score": result.fit_score})
        if args.export == "json":
            Path(args.out).write_text(json.dumps(scenarios, indent=2), encoding="utf-8")
        else:
            pd.DataFrame(scenarios).to_csv(args.out, index=False)
        return 0

    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
