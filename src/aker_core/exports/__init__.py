"""Excel export surface aligned with `openspec/specs/exports/spec.md`.

The module centralises workbook builders and sheet components so callers can
assemble investor-ready Excel packets without importing internal modules.
"""

from __future__ import annotations

from .builder import ExcelWorkbookBuilder, to_excel
from .memo_context import MemoContextBuilder
from .memo_service import MemoContextService
from .word_memo import WordMemoBuilder, to_word
from .sheets import (
    OverviewSheet,
    MarketScorecardSheet,
    AssetFitSheet,
    DealArchetypesSheet,
    RiskSheet,
    OpsKPIsSheet,
    COUTIDPatternsSheet,
    ChecklistSheet,
    DataLineageSheet,
    ConfigSheet
)

__all__ = [
    "ExcelWorkbookBuilder",
    "to_excel",
    "to_word",
    "OverviewSheet",
    "MarketScorecardSheet",
    "AssetFitSheet",
    "DealArchetypesSheet",
    "RiskSheet",
    "OpsKPIsSheet",
    "COUTIDPatternsSheet",
    "ChecklistSheet",
    "DataLineageSheet",
    "ConfigSheet",
    "MemoContextBuilder",
    "MemoContextService",
    "WordMemoBuilder",
]
