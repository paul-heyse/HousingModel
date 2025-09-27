#!/usr/bin/env python3
"""
Demonstration of Aker Supply Calculators

This script demonstrates the usage of the supply constraint calculators
for the Aker Property Model.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Import the supply calculators
from aker_core.supply import elasticity, vacancy, leaseup_tom


def demo_elasticity_calculator():
    """Demonstrate the elasticity calculator."""
    print("=== Elasticity Calculator Demo ===")

    # Sample data: 4 years of permits and households
    permits = [1200, 1350, 1100, 1400]
    households = [52000, 52500, 53000, 53500]

    print(f"Permits: {permits}")
    print(f"Households: {households}")

    # Calculate elasticity (3-year average)
    elasticity_value = elasticity(permits, households, years=3)
    print(f"Elasticity (permits per 1k households): {elasticity_value".2f"}")

    # Test with different averaging periods
    elasticity_2yr = elasticity(permits, households, years=2)
    print(f"Elasticity (2-year average): {elasticity_2yr".2f"}")

    print()


def demo_vacancy_calculator():
    """Demonstrate the vacancy calculator."""
    print("=== Vacancy Calculator Demo ===")

    # Sample HUD vacancy data
    hud_data = {
        'year': [2020, 2021, 2022],
        'vacancy_rate': [5.2, 4.8, 4.5],
        'geography': ['MSA001', 'MSA001', 'MSA001']
    }

    print(f"HUD Data: {hud_data}")

    # Calculate vacancy rate
    vacancy_rate = vacancy(hud_data)
    print(f"Vacancy Rate: {vacancy_rate".2f"}%")

    # Test with DataFrame input
    hud_df = pd.DataFrame(hud_data)
    vacancy_rate_df = vacancy(hud_df)
    print(f"Vacancy Rate (DataFrame): {vacancy_rate_df".2f"}%")

    print()


def demo_leaseup_calculator():
    """Demonstrate the lease-up time calculator."""
    print("=== Lease-Up Calculator Demo ===")

    # Sample lease data
    base_date = datetime(2023, 1, 1)
    lease_dates = [base_date + timedelta(days=i) for i in range(20)]

    lease_data = {
        'lease_date': lease_dates,
        'property_id': ['PROP001'] * 10 + ['PROP002'] * 10,
        'days_on_market': [15, 20, 25, 18, 22, 12, 16, 19, 14, 17,
                          30, 35, 40, 28, 32, 25, 29, 33, 27, 31]
    }

    print(f"Sample lease data for {len(lease_dates)} leases")

    # Calculate lease-up time
    leaseup_days = leaseup_tom(lease_data)
    print(f"Median Lease-Up Time: {leaseup_days".1f"} days")

    # Test with property filtering
    filtered_data = {
        'lease_date': lease_dates[:10],
        'property_id': ['PROP001'] * 10,
        'property_type': ['apartment'] * 10,
        'days_on_market': [15, 20, 25, 18, 22, 12, 16, 19, 14, 17]
    }

    leaseup_filtered = leaseup_tom(filtered_data, property_filters={'property_type': 'apartment'})
    print(f"Median Lease-Up Time (Apartments only): {leaseup_filtered".1f"} days")

    print()


def demo_supply_integration():
    """Demonstrate the integrated supply calculation workflow."""
    print("=== Supply Integration Demo ===")

    # Sample data for a fictional MSA
    msa_id = "DEMO001"
    data_vintage = "2023-09-15"

    # Sample permit and household data
    permits = [1200, 1350, 1100, 1400]
    households = [52000, 52500, 53000, 53500]

    # Sample HUD vacancy data
    hud_data = {
        'year': [2020, 2021, 2022],
        'vacancy_rate': [5.2, 4.8, 4.5],
        'geography': ['DEMO001', 'DEMO001', 'DEMO001'],
        'vacancy_type': ['rental', 'rental', 'rental'],
        'source': ['HUD', 'HUD', 'HUD']
    }

    # Sample lease data
    lease_data = {
        'lease_date': pd.date_range('2023-01-01', periods=50, freq='D'),
        'property_id': ['PROP001'] * 25 + ['PROP002'] * 25,
        'days_on_market': np.random.randint(10, 60, 50).tolist()
    }

    # Calculate individual metrics
    elasticity_value = elasticity(permits, households, years=3)
    vacancy_value = vacancy(hud_data)
    leaseup_value = leaseup_tom(lease_data, time_window_days=90)

    print(f"MSA: {msa_id}")
    print(f"Elasticity: {elasticity_value".2f"} permits per 1k households")
    print(f"Vacancy Rate: {vacancy_value".2f"}%")
    print(f"Lease-Up Time: {leaseup_value".1f"} days")

    # Show inverse scoring (for integration with pillar scoring)
    from aker_core.supply import inverse_elasticity_score, inverse_vacancy_score, inverse_leaseup_score

    elasticity_score = inverse_elasticity_score(elasticity_value)
    vacancy_score = inverse_vacancy_score(vacancy_value)
    leaseup_score = inverse_leaseup_score(leaseup_value)

    print("
Inverse Scores (0-100, higher = more constrained):")
    print(f"Elasticity Score: {elasticity_score".1f"}")
    print(f"Vacancy Score: {vacancy_score".1f"}")
    print(f"Lease-Up Score: {leaseup_score".1f"}")

    # Composite supply score
    composite_score = (elasticity_score + vacancy_score + leaseup_score) / 3
    print(f"Composite Supply Score: {composite_score".1f"}")

    print()


def main():
    """Run all demonstrations."""
    print("Aker Supply Calculators Demonstration")
    print("=" * 50)
    print()

    demo_elasticity_calculator()
    demo_vacancy_calculator()
    demo_leaseup_calculator()
    demo_supply_integration()

    print("Demonstration complete!")


if __name__ == "__main__":
    main()
