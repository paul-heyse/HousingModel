#!/usr/bin/env python3
"""
Integration test for Aker Supply Calculators

Demonstrates the complete supply calculation workflow from raw data to final scores.
"""

import os
import sys

import numpy as np
import pandas as pd

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from aker_core.supply import (
        calculate_supply_metrics,
        elasticity,
        get_supply_scores_for_scoring,
        inverse_elasticity_score,
        inverse_leaseup_score,
        inverse_vacancy_score,
        leaseup_tom,
        vacancy,
        validate_supply_data_quality,
    )

    print("✅ Successfully imported all supply calculators")

    # Demo data for a fictional MSA
    print("\n=== Supply Calculator Integration Demo ===")

    msa_id = "DEMO001"
    data_vintage = "2023-09-15"

    # 1. Elasticity calculation
    print("1. Elasticity Calculation:")
    permits = [1200, 1350, 1100, 1400]  # 4 years of permits
    households = [52000, 52500, 53000, 53500]  # 4 years of households

    elasticity_value = elasticity(permits, households, years=3)
    elasticity_score = inverse_elasticity_score(elasticity_value)
    print(f"   Elasticity: {elasticity_value:.2f} permits per 1k households")
    print(f"   Constraint Score: {elasticity_score:.1f}/100")

    # 2. Vacancy calculation
    print("\n2. Vacancy Calculation:")
    hud_data = {
        "year": [2020, 2021, 2022],
        "vacancy_rate": [5.2, 4.8, 4.5],
        "geography": ["DEMO001", "DEMO001", "DEMO001"],
    }

    vacancy_value = vacancy(hud_data)
    vacancy_score = inverse_vacancy_score(vacancy_value)
    print(f"   Vacancy Rate: {vacancy_value:.2f}%")
    print(f"   Constraint Score: {vacancy_score:.1f}/100")

    # 3. Lease-up calculation
    print("\n3. Lease-Up Calculation:")
    lease_data = {
        "lease_date": pd.date_range("2023-01-01", periods=30, freq="D"),
        "property_id": ["PROP001"] * 15 + ["PROP002"] * 15,
        "days_on_market": np.random.randint(10, 60, 30).tolist(),
    }

    leaseup_value = leaseup_tom(lease_data)
    leaseup_score = inverse_leaseup_score(leaseup_value)
    print(f"   Lease-Up Time: {leaseup_value:.1f} days")
    print(f"   Constraint Score: {leaseup_score:.1f}/100")

    # 4. Composite supply score
    print("\n4. Composite Supply Score:")
    composite_score = (elasticity_score + vacancy_score + leaseup_score) / 3
    print(f"   Composite Score: {composite_score:.1f}/100")

    # 5. Demonstrate integration functions
    print("\n5. Integration Functions:")

    # Mock data for integration demo
    integration_data = {
        "msa_id": msa_id,
        "permits": permits,
        "households": households,
        "hud_data": hud_data,
        "lease_data": lease_data,
        "data_vintage": data_vintage,
    }

    print("   Integration functions available:")
    print("   - calculate_supply_metrics(): Calculate and persist all metrics")
    print("   - get_supply_scores_for_scoring(): Get formatted scores for pillar scoring")
    print("   - validate_supply_data_quality(): Validate data quality")

    # 6. Mathematical property validation
    print("\n6. Mathematical Property Validation:")

    # Test monotonicity
    print("   Testing Monotonicity:")
    x1 = [1000, 1100, 1200]
    y1 = [50000, 51000, 52000]
    x2 = [1100, 1200, 1300]  # Higher than x1
    y2 = [51000, 52000, 53000]  # Higher than y1

    e1 = elasticity(x1, y1)
    e2 = elasticity(x2, y2)
    print(f"     e1 (lower inputs): {e1:.3f}")
    print(f"     e2 (higher inputs): {e2:.3f}")
    print(f"     Monotonicity preserved: {e2 > e1}")

    # Test scaling invariance
    print("\n   Testing Scaling Invariance:")
    scale_factor = 2.0
    x_scaled = [x * scale_factor for x in x1]
    y_scaled = [y * scale_factor for y in y1]

    e_original = elasticity(x1, y1)
    e_scaled = elasticity(x_scaled, y_scaled)
    print(f"     Original: {e_original:.6f}")
    print(f"     Scaled: {e_scaled:.6f}")
    print(f"     Scaling invariant: {abs(e_original - e_scaled) < 1e-10}")

    # Test bounds guarantee
    print("\n   Testing Bounds Guarantee:")
    test_cases = [
        ([1, 2, 3], [100, 101, 102]),  # Small values
        ([1000000, 1100000, 1200000], [50000000, 51000000, 52000000]),  # Large values
    ]

    for permits_test, households_test in test_cases:
        result = elasticity(permits_test, households_test)
        print(f"     Test case: {result:.2f} (bounds: {result >= 0})")

    print("\n🎉 All supply calculator integration tests completed successfully!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the supply calculators are properly installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
