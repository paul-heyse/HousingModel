"""Deal API surface.

Re-exports the ranking interface and types from :mod:`aker_deal` so callers
can use ``deal.rank_scopes(...)`` as specified.
"""

from aker_deal import (
    RankConfig,
    RankedScope,
    ScopeTemplate,
    deal_archetype,
    rank_scopes,
    rank_scopes_with_etl,
)

__all__ = [
    "ScopeTemplate",
    "RankedScope",
    "RankConfig",
    "deal_archetype",
    "rank_scopes",
    "rank_scopes_with_etl",
]


