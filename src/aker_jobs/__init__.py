"""Innovation and jobs analysis utilities."""

from .metrics import (
    ExpansionEvent,
    aggregate_migration_to_msa,
    awards_per_100k,
    awards_trend,
    business_formation_rate,
    business_survival_trend,
    classify_expansion,
    compute_trend,
    location_quotient,
    migration_net_25_44,
    summarise_expansions,
)
from .sources import (
    DataIntegrationError,
    fetch_census_bfs,
    fetch_expansion_events,
    fetch_irs_migration,
    fetch_nih_reporter_projects,
    fetch_nsf_awards,
    fetch_usaspending_contracts,
)
from .timeseries import cagr

__all__ = [
    "ExpansionEvent",
    "awards_per_100k",
    "awards_trend",
    "business_formation_rate",
    "business_survival_trend",
    "classify_expansion",
    "compute_trend",
    "location_quotient",
    "migration_net_25_44",
    "summarise_expansions",
    "aggregate_migration_to_msa",
    "cagr",
    "fetch_census_bfs",
    "fetch_irs_migration",
    "fetch_nih_reporter_projects",
    "fetch_nsf_awards",
    "fetch_usaspending_contracts",
    "fetch_expansion_events",
    "DataIntegrationError",
]
