#!/usr/bin/env python3
"""Quality gate validation script for CI/CD pipelines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aker_core.validation import (
    GreatExpectationsValidator,
    ValidationResult,
    get_validation_suites_dir,
    list_available_suites,
    validate_dataset,
)


def run_quality_gate(
    dataset_type: str,
    data_file: str,
    suite_name: str = None,
    fail_on_error: bool = True,
    output_file: str = None
) -> Dict[str, any]:
    """Run quality gate validation on a dataset.

    Args:
        dataset_type: Type of dataset ("acs", "market_data", etc.)
        data_file: Path to data file (CSV, Parquet, etc.)
        suite_name: Optional specific suite name to use
        fail_on_error: If True, exit with error code on validation failures
        output_file: Optional file to write detailed results

    Returns:
        Dictionary with validation results
    """
    print(f"🛡️ Running quality gate validation for {dataset_type} dataset")

    try:
        # Load data
        if data_file.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(data_file)
        elif data_file.endswith('.parquet'):
            import pandas as pd
            df = pd.read_parquet(data_file)
        else:
            raise ValueError(f"Unsupported file format: {data_file}")

        print(f"📊 Loaded {len(df)} records from {data_file}")

        # Determine suite name
        if suite_name is None:
            # Map dataset type to suite name
            suite_mapping = {
                "acs": "acs_income_validation",
                "market_data": "market_data_validation",
                "census": "acs_income_validation",
            }
            suite_name = suite_mapping.get(dataset_type.lower())

        if not suite_name:
            raise ValueError(f"No validation suite found for dataset type: {dataset_type}")

        print(f"🔍 Validating using suite: {suite_name}")

        # Run validation
        validator = GreatExpectationsValidator()
        result = validator.validate_dataframe(df, suite_name)

        # Generate report
        report = {
            "dataset_type": dataset_type,
            "data_file": data_file,
            "suite_name": suite_name,
            "validation_success": result.success,
            "total_expectations": result.total_expectations,
            "successful_expectations": result.successful_expectations,
            "failed_expectations": len(result.failed_expectations),
            "failure_rate": result.failure_rate,
            "failed_details": result.failed_expectations,
            "timestamp": result.results[0].meta.get("run_id", "unknown") if result.results else "unknown"
        }

        # Print summary
        print("
✅ Quality Gate Results:"        print(f"   Total Expectations: {report['total_expectations']}")
        print(f"   Successful: {report['successful_expectations']}")
        print(f"   Failed: {report['failed_expectations']}")
        print(f"   Success Rate: {(1 - report['failure_rate']) * 100".1f"}%")

        if result.failed_expectations:
            print("
❌ Failed Expectations:"            for failure in result.failed_expectations[:5]:  # Show first 5
                print(f"   - {failure['expectation_type']}: {failure['message']}")
            if len(result.failed_expectations) > 5:
                print(f"   ... and {len(result.failed_expectations) - 5} more")

        # Save detailed results if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Detailed results saved to: {output_file}")

        # Exit with appropriate code
        if fail_on_error and not result.success:
            print(f"\n❌ Quality gate failed: {len(result.failed_expectations)} expectations failed")
            sys.exit(1)
        elif result.success:
            print("\n✅ Quality gate passed: All expectations met")
            sys.exit(0)
        else:
            print(f"\n⚠️ Quality gate passed with warnings: {len(result.failed_expectations)} expectations failed")
            sys.exit(0)

        return report

    except Exception as e:
        print(f"❌ Quality gate execution failed: {e}")
        if fail_on_error:
            sys.exit(1)
        raise


def list_suites() -> None:
    """List all available validation suites."""
    suites = list_available_suites()
    print("Available validation suites:")
    for suite in suites:
        print(f"  - {suite}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Quality gate validation for CI/CD pipelines")
    parser.add_argument(
        "dataset_type",
        help="Type of dataset to validate (acs, market_data, etc.)"
    )
    parser.add_argument(
        "data_file",
        help="Path to data file to validate"
    )
    parser.add_argument(
        "--suite",
        help="Specific suite name to use (defaults to dataset type mapping)"
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Don't fail on validation errors (for monitoring)"
    )
    parser.add_argument(
        "--output",
        help="File to write detailed validation results"
    )
    parser.add_argument(
        "--list-suites",
        action="store_true",
        help="List available validation suites and exit"
    )

    args = parser.parse_args()

    if args.list_suites:
        list_suites()
        return

    try:
        result = run_quality_gate(
            dataset_type=args.dataset_type,
            data_file=args.data_file,
            suite_name=args.suite,
            fail_on_error=not args.no_fail,
            output_file=args.output
        )
        return result

    except Exception as e:
        print(f"❌ Quality gate failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
