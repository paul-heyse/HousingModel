#!/usr/bin/env python3
"""
Test script for Aker Supply Calculators

Verifies that the supply constraint calculators work correctly.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import numpy as np
    import pandas as pd
    from aker_core.supply import elasticity, vacancy, leaseup_tom

    print("✅ Successfully imported supply calculators")

    # Test elasticity calculator
    print("\n=== Testing Elasticity Calculator ===")
    permits = [1200, 1350, 1100, 1400]
    households = [52000, 52500, 53000, 53500]

    try:
        elasticity_value = elasticity(permits, households, years=3)
        print(f"✅ Elasticity calculation successful: {elasticity_value".2f"}")
    except Exception as e:
        print(f"❌ Elasticity calculation failed: {e}")

    # Test vacancy calculator
    print("\n=== Testing Vacancy Calculator ===")
    hud_data = {
        'year': [2020, 2021, 2022],
        'vacancy_rate': [5.2, 4.8, 4.5],
        'geography': ['MSA001', 'MSA001', 'MSA001']
    }

    try:
        vacancy_rate = vacancy(hud_data)
        print(f"✅ Vacancy calculation successful: {vacancy_rate".2f"}%")
    except Exception as e:
        print(f"❌ Vacancy calculation failed: {e}")

    # Test lease-up calculator
    print("\n=== Testing Lease-Up Calculator ===")
    import pandas as pd
    lease_data = {
        'lease_date': pd.date_range('2023-01-01', periods=20, freq='D'),
        'property_id': ['PROP001'] * 10 + ['PROP002'] * 10,
        'days_on_market': [15, 20, 25, 18, 22, 12, 16, 19, 14, 17,
                          30, 35, 40, 28, 32, 25, 29, 33, 27, 31]
    }

    try:
        leaseup_days = leaseup_tom(lease_data)
        print(f"✅ Lease-up calculation successful: {leaseup_days".1f"} days")
    except Exception as e:
        print(f"❌ Lease-up calculation failed: {e}")

    # Test error handling
    print("\n=== Testing Error Handling ===")

    # Test insufficient data
    try:
        elasticity([1000], [50000], years=3)
        print("❌ Should have failed for insufficient data")
    except ValueError as e:
        print(f"✅ Correctly caught insufficient data error: {str(e)[:50]}...")

    # Test zero households
    try:
        elasticity([1000, 1100, 1200], [50000, 0, 52000])
        print("❌ Should have failed for zero households")
    except ZeroDivisionError as e:
        print(f"✅ Correctly caught zero households error: {e}")

    # Test negative permits
    try:
        elasticity([1000, -100, 1200], [50000, 51000, 52000])
        print("❌ Should have failed for negative permits")
    except ValueError as e:
        print(f"✅ Correctly caught negative permits error: {str(e)[:50]}...")

    print("\n🎉 All supply calculator tests completed!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the dependencies are installed: numpy, pandas")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
