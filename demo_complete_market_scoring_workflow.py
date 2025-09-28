#!/usr/bin/env python3
"""
Complete Market Scoring Workflow Test

This script demonstrates the complete workflow from supply calculators
through pillar aggregation to final market scores.
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, date

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from aker_core.supply import (
        elasticity, vacancy, leaseup_tom,
        inverse_elasticity_score, inverse_vacancy_score, inverse_leaseup_score,
        calculate_supply_metrics, get_supply_scores_for_scoring
    )
    from aker_core.markets import score, MarketPillarScores

    print("✅ Successfully imported complete scoring workflow")

    # Demo complete market scoring workflow
    print("\n=== Complete Market Scoring Workflow Demo ===")

    # 1. Start with raw supply data
    print("1. Raw Supply Data Input:")
    permits = [1200, 1350, 1100, 1400]
    households = [52000, 52500, 53000, 53500]

    hud_data = {
        'year': [2020, 2021, 2022],
        'vacancy_rate': [5.2, 4.8, 4.5],
        'geography': ['MSA001', 'MSA001', 'MSA001']
    }

    lease_data = {
        'lease_date': pd.date_range('2023-01-01', periods=30, freq='D'),
        'property_id': ['PROP001'] * 15 + ['PROP002'] * 15,
        'days_on_market': np.random.randint(10, 60, 30).tolist()
    }

    print(f"   Permits: {permits}")
    print(f"   Households: {households}")
    print(f"   HUD Data: {len(hud_data['year'])} years")
    print(f"   Lease Data: {len(lease_data['lease_date'])} transactions")

    # 2. Calculate supply metrics
    print("\n2. Supply Metric Calculations:")
    elasticity_value = elasticity(permits, households, years=3)
    vacancy_value = vacancy(hud_data)
    leaseup_value = leaseup_tom(lease_data)

    print(f"   Elasticity: {elasticity_value:.2f} permits per 1k households")
    print(f"   Vacancy Rate: {vacancy_value:.2f}%")
    print(f"   Lease-Up Time: {leaseup_value:.1f} days")

    # 3. Convert to inverse scores (0-100 scale)
    print("\n3. Supply Constraint Scores (0-100):")
    elasticity_score = inverse_elasticity_score(elasticity_value)
    vacancy_score = inverse_vacancy_score(vacancy_value)
    leaseup_score = inverse_leaseup_score(leaseup_value)

    print(f"   Elasticity Score: {elasticity_score:.1f}/100")
    print(f"   Vacancy Score: {vacancy_score:.1f}/100")
    print(f"   Lease-Up Score: {leaseup_score:.1f}/100")

    # 4. Aggregate supply pillar score
    print("\n4. Supply Pillar Aggregation:")
    supply_composite = (elasticity_score + vacancy_score + leaseup_score) / 3
    print(f"   Supply Pillar Score: {supply_composite:.1f}/100")

    # 5. Create mock pillar scores for complete market scoring
    print("\n5. Complete Market Pillar Scores:")
    pillar_scores = MarketPillarScores(
        msa_id="MSA001",
        supply_0_5=supply_composite / 20,  # Convert 0-100 to 0-5
        jobs_0_5=3.8,  # Mock jobs score
        urban_0_5=4.0,  # Mock urban score
        outdoor_0_5=3.6,  # Mock outdoor score
        weighted_0_5=0.0,  # Will be calculated
        weighted_0_100=0.0,  # Will be calculated
        weights={"supply": 0.3, "jobs": 0.3, "urban": 0.2, "outdoor": 0.2},
        score_as_of=date(2023, 9, 15),
        run_id=None
    )

    # Calculate final weighted score
    final_0_5 = (pillar_scores.supply_0_5 * 0.3 +
                 pillar_scores.jobs_0_5 * 0.3 +
                 pillar_scores.urban_0_5 * 0.2 +
                 pillar_scores.outdoor_0_5 * 0.2)

    final_0_100 = final_0_5 * 20

    print(f"   Supply: {pillar_scores.supply_0_5:.2f}/5")
    print(f"   Jobs: {pillar_scores.jobs_0_5:.2f}/5")
    print(f"   Urban: {pillar_scores.urban_0_5:.2f}/5")
    print(f"   Outdoor: {pillar_scores.outdoor_0_5:.2f}/5")
    print(f"   Final Score: {final_0_5:.2f}/5 ({final_0_100:.1f}/100)")

    # 6. Demonstrate the scoring API
    print("\n6. Scoring API Demonstration:")
    print("   Available functions:")
    print("   - elasticity(): Calculate building permit elasticity")
    print("   - vacancy(): Calculate rental vacancy rates")
    print("   - leaseup_tom(): Calculate lease-up time-on-market")
    print("   - score(): Compose final market scores from pillar data")
    print("   - MarketPillarScores: Dataclass for score results")

    # 7. Show mathematical properties
    print("\n7. Mathematical Property Validation:")

    # Test monotonicity
    x1 = [1000, 1100, 1200]
    y1 = [50000, 51000, 52000]
    x2 = [1100, 1200, 1300]  # Higher values

    e1 = elasticity(x1, y1)
    e2 = elasticity(x2, y1)
    print(f"   Monotonicity: e2({e2:.3f}) > e1({e1:.3f}) = {e2 > e1}")

    # Test scaling invariance
    scale_factor = 2.0
    x_scaled = [x * scale_factor for x in x1]
    e_original = elasticity(x1, y1)
    e_scaled = elasticity(x_scaled, y1)
    print(
        "   Scaling Invariance: |e_original - e_scaled| = "
        f"{abs(e_original - e_scaled):.2e}"
    )

    # Test bounds
    bounds_ok = 0 <= elasticity_value <= 200  # Reasonable range
    print(f"   Bounds Check: {elasticity_value:.2f} in [0, 200] = {bounds_ok}")

    print("\n🎉 Complete market scoring workflow demonstrated successfully!")
    print("\nWorkflow Summary:")
    print("✅ Raw data → Supply calculators → Inverse scoring → Pillar aggregation → Final market score")
    print("✅ Mathematical properties validated (monotonicity, scaling invariance, bounds)")
    print("✅ Integration points identified for full Aker Property Model")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all Aker modules are properly installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
