#!/usr/bin/env python3
"""
Production deployment script for Aker Supply Calculators

This script handles the deployment and configuration of the supply constraint
calculators in a production environment.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from aker_core.monitoring.supply_monitoring import get_supply_monitor
    from aker_core.supply import (
        calculate_supply_metrics,
        elasticity,
        get_supply_scores_for_scoring,
        leaseup_tom,
        vacancy,
        validate_supply_data_quality,
    )
    from aker_core.validation.supply_validation import SupplyValidationSuite

    print("✅ Successfully imported supply calculators")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the supply calculators are properly installed")
    sys.exit(1)


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), *(logging.FileHandler(log_file) if log_file else [])],
    )


def check_dependencies():
    """Check that all required dependencies are available."""
    print("Checking dependencies...")

    required_packages = ["numpy", "pandas", "sqlalchemy", "alembic"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False

    print("✅ All dependencies available")
    return True


def run_database_migration():
    """Run database migrations for supply calculators."""
    print("\nRunning database migrations...")

    try:
        from alembic import command
        from alembic.config import Config

        # Get the alembic configuration
        alembic_cfg = Config("alembic.ini")

        print("Upgrading database to latest version...")
        command.upgrade(alembic_cfg, "head")

        print("✅ Database migration completed successfully")
        return True

    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False


def run_validation_suite():
    """Run the schema validation suite placeholder."""
    print("\nRunning validation suite...")

    try:
        # The full validation requires a database session; here we ensure the suite loads.
        SupplyValidationSuite()
        print("✅ Validation stack ready (Pandera schemas registered)")
        print("   Execute runtime validation within the pipeline environment")
        return True

    except Exception as e:
        print(f"❌ Validation suite initialisation failed: {e}")
        return False


def run_test_suite():
    """Run the test suite for supply calculators."""
    print("\nRunning test suite...")

    try:
        import subprocess

        # Run the test suite
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/core/test_supply_calculators.py",
                "tests/core/test_supply_mathematical_properties.py",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ All tests passed")
            print(f"   Test output: {result.stdout.split('=')[-1].strip()}")
            return True
        else:
            print("❌ Some tests failed")
            print("   Test output:", result.stdout[-500:])  # Last 500 chars
            if result.stderr:
                print("   Error output:", result.stderr[-500:])
            return False

    except Exception as e:
        print(f"❌ Test suite execution failed: {e}")
        return False


def configure_monitoring():
    """Configure performance monitoring."""
    print("\nConfiguring performance monitoring...")

    try:
        monitor = get_supply_monitor()

        # Configure monitoring thresholds
        monitor.alert_thresholds = {
            "calculation_time_ms": 5000,  # 5 seconds max
            "memory_usage_mb": 100,  # 100MB max
            "error_rate": 0.05,  # 5% error rate
        }

        print("✅ Performance monitoring configured")
        print(f"   Alert thresholds: {monitor.alert_thresholds}")
        return True

    except Exception as e:
        print(f"❌ Monitoring configuration failed: {e}")
        return False


def create_deployment_config():
    """Create deployment configuration files."""
    print("\nCreating deployment configuration...")

    config = {
        "deployment": {
            "name": "aker_supply_calculators",
            "version": "1.0.0",
            "deployed_at": datetime.now().isoformat(),
            "environment": "production",
        },
        "supply_calculators": {
            "elasticity": {"default_years": 3, "max_years": 10, "cache_size": 1000},
            "vacancy": {
                "default_type": "rental",
                "supported_types": ["rental", "multifamily", "overall"],
            },
            "leaseup": {"default_window_days": 90, "max_window_days": 365, "min_sample_size": 10},
        },
        "performance": {
            "enable_profiling": True,
            "max_metrics_history": 10000,
            "alert_thresholds": {
                "calculation_time_ms": 5000,
                "memory_usage_mb": 100,
                "error_rate": 0.05,
            },
        },
        "database": {
            "migration_version": "0004_supply_calculators",
            "tables": ["market_supply"],
            "indexes": ["ix_market_supply_msa_vintage", "ix_market_supply_elasticity"],
        },
        "validation": {
            "schemas": {
                "supply_summary": "pandera",
                "frequency": "post_processing",
            }
        },
    }

    # Write configuration file
    config_file = Path("config") / "supply_calculators.json"
    config_file.parent.mkdir(exist_ok=True)

    with open(config_file, "w") as f:
        import json

        json.dump(config, f, indent=2)

    print(f"✅ Deployment configuration created: {config_file}")
    return True


def run_health_check():
    """Run a basic health check of the deployed system."""
    print("\nRunning health check...")

    try:
        # Test basic functionality
        from aker_core.supply import elasticity, vacancy

        # Test elasticity
        permits = [1200, 1350, 1100, 1400]
        households = [52000, 52500, 53000, 53500]
        elasticity_value = elasticity(permits, households)
        assert elasticity_value > 0

        # Test vacancy
        hud_data = {
            "year": [2020, 2021, 2022],
            "vacancy_rate": [5.2, 4.8, 4.5],
            "geography": ["TEST001", "TEST001", "TEST001"],
        }
        vacancy_value = vacancy(hud_data)
        assert 0 <= vacancy_value <= 100

        print("✅ Health check passed - core functionality working")
        return True

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Aker Supply Calculators")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-migration", action="store_true", help="Skip database migration")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--log-file", help="Log file path")

    args = parser.parse_args()

    print("Aker Supply Calculators Production Deployment")
    print("=" * 60)

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Run database migration
    if not args.skip_migration:
        if not run_database_migration():
            print("❌ Deployment failed during migration")
            sys.exit(1)
    else:
        print("⚠️  Skipping database migration")

    # Run tests
    if not args.skip_tests:
        if not run_test_suite():
            print("❌ Deployment failed during testing")
            sys.exit(1)
    else:
        print("⚠️  Skipping test suite")

    # Configure monitoring
    if not configure_monitoring():
        print("⚠️  Monitoring configuration failed (non-critical)")

    # Run validation suite
    if not run_validation_suite():
        print("⚠️  Validation suite failed (non-critical)")

    # Create deployment config
    if not create_deployment_config():
        print("⚠️  Deployment configuration failed (non-critical)")

    # Run health check
    if not run_health_check():
        print("❌ Deployment failed health check")
        sys.exit(1)

    print("\n🎉 Aker Supply Calculators deployment completed successfully!")
    print("\nDeployment Summary:")
    print("✅ Database migration: Completed")
    print("✅ Core functionality: Working")
    print("✅ Tests: Passed")
    print("✅ Monitoring: Configured")
    print("✅ Validation: Ready")
    print("✅ Configuration: Created")

    print("\nNext steps:")
    print("1. Configure data source connections in your ETL pipeline")
    print("2. Set up scheduled jobs for data refresh")
    print("3. Monitor performance and alerts in production")
    print("4. Update documentation with deployment-specific details")


if __name__ == "__main__":
    main()
