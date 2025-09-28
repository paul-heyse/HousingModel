from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aker_core.database.ops import OpsRepository
from aker_core.ops import optimize_cadence, pricing_rules, reputation_index


def optimize_cadence_cmd(units: int, downtime_wk: int, vacancy_cap: float, out: str) -> int:
    """CLI command for renovation cadence optimization."""
    plan = optimize_cadence(units, downtime_wk, vacancy_cap)
    Path(out).write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
    print(f"Optimized schedule saved to {out}")
    print(f"Total weeks: {plan.total_weeks}")
    print(f"Weekly schedule: {plan.weekly_schedule}")
    print(f"Max vacancy rate: {plan.max_vacancy_rate:.2%}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OPS tools CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Reputation index command
    rep_parser = subparsers.add_parser("reputation", help="Calculate reputation index")
    rep_parser.add_argument("reviews_json", help="Path to reviews JSON array")
    rep_parser.add_argument("nps", type=float, help="NPS value (-100..100)")
    rep_parser.add_argument("--out", default="ops_rules.json")
    rep_parser.add_argument("--db", help="Optional DB URL for persistence")
    rep_parser.add_argument("--asset-id", type=int, help="Asset ID for persistence")

    # Cadence optimization command
    cadence_parser = subparsers.add_parser("optimize-cadence", help="Optimize renovation cadence")
    cadence_parser.add_argument("units", type=int, help="Total units to renovate")
    cadence_parser.add_argument("downtime_wk", type=int, help="Downtime weeks per unit")
    cadence_parser.add_argument("vacancy_cap", type=float, help="Maximum vacancy rate (0.0-1.0)")
    cadence_parser.add_argument("--out", default="cadence_plan.json")

    args = parser.parse_args(argv)

    if args.command == "reputation":
        reviews = json.loads(Path(args.reviews_json).read_text(encoding="utf-8"))
        idx = reputation_index(reviews, args.nps)
        rules = pricing_rules(idx)

        Path(args.out).write_text(json.dumps({"index": idx, "rules": rules}, indent=2), encoding="utf-8")

        if args.db and args.asset_id:
            engine = create_engine(args.db)
            with Session(engine) as session:
                OpsRepository(session).upsert_index(
                    asset_id=args.asset_id,
                    nps=int(args.nps),
                    reputation_idx=idx,
                )
                session.commit()
        return 0

    elif args.command == "optimize-cadence":
        return optimize_cadence_cmd(args.units, args.downtime_wk, args.vacancy_cap, args.out)

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

