#!/usr/bin/env python3
"""Quality gate validation script for CI/CD pipelines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd

from aker_core.validation import ValidationResult, list_available_suites, validate_dataset


def run_quality_gate(
    dataset_type: str,
    data_file: str,
    *,
    fail_on_error: bool = True,
    output_file: str | None = None,
) -> Dict[str, Any]:
    """Run schema validation on a dataset."""

    print(f"🛡️ Running quality gate validation for '{dataset_type}' using {data_file}")

    if data_file.endswith(".csv"):
        df = pd.read_csv(data_file)
    elif data_file.endswith(".parquet"):
        df = pd.read_parquet(data_file)
    else:
        raise ValueError(f"Unsupported file format: {data_file}")

    print(f"📊 Loaded {len(df)} records from {data_file}")

    result: ValidationResult = validate_dataset(df, dataset_type)
    payload = result.to_dict()

    print("\n✅ Validation Summary:" if result.success else "\n❌ Validation Summary:")
    print(f"   Dataset Type: {dataset_type}")
    print(f"   Rows Validated: {payload['validated_rows']}")
    print(
        f"   Checks: {payload['successful_expectations']}/{payload['total_expectations']}"
    )
    print(f"   Failure Rate: {payload['failure_rate'] * 100:.2f}%")

    if payload["failures"]:
        print("\nDetails (first 5 failures):")
        for failure in payload["failures"][:5]:
            column = failure.get("column") or "<row>"
            check = failure.get("check") or "unknown_check"
            message = failure.get("message") or failure.get("failure_case") or ""
            print(f"   - {column}: {check} :: {message}")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
        print(f"\n📄 Detailed results saved to {output_file}")

    if fail_on_error and not result.success:
        print("\n❌ Quality gate failed: validation errors detected")
        sys.exit(1)

    if result.success:
        print("\n✅ Quality gate passed: all checks satisfied")
    else:
        print("\n⚠️ Quality gate completed with warnings")

    return payload


def list_suites() -> None:
    """List all available dataset types registered with the validator."""
    suites = list_available_suites()
    print("Registered validation datasets:")
    for suite in suites:
        print(f"  - {suite}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Quality gate validation for CI/CD pipelines")
    parser.add_argument("dataset_type", help="Dataset type to validate (e.g. acs, market_data)")
    parser.add_argument("data_file", help="Path to CSV or Parquet file to validate")
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Do not exit with error code when validation fails",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write a JSON report",
    )
    parser.add_argument(
        "--list-suites",
        action="store_true",
        help="List available dataset types and exit",
    )

    args = parser.parse_args()

    if args.list_suites:
        list_suites()
        return

    run_quality_gate(
        dataset_type=args.dataset_type,
        data_file=args.data_file,
        fail_on_error=not args.no_fail,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
