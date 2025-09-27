# Innovation & Jobs Analytics

This module provides reusable calculators and data integrations that power the
*Market Jobs* pillar. The helpers live under `aker_jobs` and are designed to be
composed inside ETL pipelines or interactive notebooks.

## NAICS Sector Mappings

The LQ/CAGR utilities assume the following high-level sector groups:

| Sector Key      | NAICS Coverage (illustrative) |
|-----------------|--------------------------------|
| `technology`    | 51, 54                         |
| `health`        | 62                             |
| `education`     | 61                             |
| `manufacturing` | 31-33                          |
| `defense`       | 9281, 3364                     |
| `biotech`       | 3254, 5417                     |

Adjust or extend these groupings upstream before calling
`aker_jobs.metrics.location_quotient`.

## Quick Start

```python
from aker_jobs import (
    fetch_census_bfs,
    fetch_nih_reporter_projects,
    awards_trend,
    business_formation_rate,
    location_quotient,
    migration_net_25_44,
)

bfs = fetch_census_bfs(state="06", start=2021, end=2023)
formation_metrics = business_formation_rate(
    bfs.rename(columns={"BFN": "formations", "time": "year"}),
    formations_column="formations",
    population_column="population",
)

lq = location_quotient(naics_counts_df, population_column="population")
net_migration = migration_net_25_44(migration_df)
nih_trend = awards_trend(nih_awards_df, periods=1)
```

## API Reference

- **Location Quotient**: `aker_jobs.metrics.location_quotient`
- **Migration Aggregation**: `aker_jobs.metrics.aggregate_migration_to_msa`
- **CAGR**: `aker_jobs.timeseries.cagr`
- **Awards Trend**: `aker_jobs.metrics.awards_trend`
- **Business Formation**: `aker_jobs.metrics.business_formation_rate`
- **Expansion Events**: `aker_jobs.sources.fetch_expansion_events`
- **External Sources**: see `aker_jobs.sources` for BFS, IRS migration, NIH, NSF,
  USAspending integrations.

Each function exposes comprehensive docstrings with parameter details and
return types.

## Usage Notes

- Ensure county-to-MSA crosswalks are kept current (OMB releases updates
  periodically).
- When performing trend analysis, supply clean date columns (quarter `Q` or
  year `Y`). The helper will attempt to coerce numeric years automatically.
- Award and survival trends return period-by-period percentage change; chain
  them into dashboards or GE validations for automated monitoring.

## Further Reading

- [Census Business Formation Series](https://www.census.gov/econ/bfs/)
- [IRS Migration Data](https://www.irs.gov/statistics/soi-tax-stats-migration-data)
- [NIH RePORTER API](https://api.reporter.nih.gov/)
- [NSF Awards API](https://www.nsf.gov/awards/about.jsp)
- [USAspending API](https://api.usaspending.gov/)
