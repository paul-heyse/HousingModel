#!/usr/bin/env python3
"""Script to run ETL flows locally for development and testing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flows.refresh_market_data import refresh_market_data
from flows.score_all_markets import score_all_markets


def main():
    """Run ETL flows locally."""
    parser = argparse.ArgumentParser(description="Run ETL flows locally")
    parser.add_argument(
        "flow",
        choices=["refresh", "score", "both"],
        help="Flow to run"
    )
    parser.add_argument(
        "--year",
        default="2022",
        help="Year for market data refresh (default: 2022)"
    )
    parser.add_argument(
        "--as-of",
        help="As-of date for partitioning (YYYY-MM format)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running"
    )

    args = parser.parse_args()

    print(f"Running ETL flows locally (dry-run: {args.dry_run})")

    try:
        if args.flow in ["refresh", "both"]:
            print(f"\n{'='*50}")
            print("REFRESH MARKET DATA FLOW")
            print(f"{'='*50}")

            if args.dry_run:
                print(f"Would run: refresh_market_data(year='{args.year}', as_of='{args.as_of}')"
            else:
                result = refresh_market_data(year=args.year, as_of=args.as_of)
                print(f"✅ Market data refresh completed: {result}")

        if args.flow in ["score", "both"]:
            print(f"\n{'='*50}")
            print("SCORE ALL MARKETS FLOW")
            print(f"{'='*50}")

            if args.dry_run:
                print(f"Would run: score_all_markets(as_of='{args.as_of}')"
            else:
                result = score_all_markets(as_of=args.as_of)
                print(f"✅ Market scoring completed: {result}")

        print(f"\n{'='*50}")
        print("ALL FLOWS COMPLETED SUCCESSFULLY")
        print(f"{'='*50}")

    except Exception as e:
        print(f"❌ Flow execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
