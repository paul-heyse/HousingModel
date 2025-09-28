"""Market scoring flow - scores all markets using latest data and models."""

from __future__ import annotations

import pandas as pd

from aker_core.validation import validate_data_quality
from aker_data.lake import DataLake

from .base import ETLFlow, etl_task, timed_flow, with_run_context


class MarketScoringFlow(ETLFlow):
    """Flow for scoring all markets using latest data and models."""

    def __init__(self):
        super().__init__("score_all_markets", "Score all markets using latest data and models")

    @etl_task("load_market_data", "Load latest market data from data lake")
    def load_market_data(self, as_of: str) -> pd.DataFrame:
        """Load market data from data lake."""
        lake = DataLake()

        # Load latest census income data
        df = lake.read("census_income", as_of=as_of)

        self.logger.info(f"Loaded {len(df)} market records from data lake")
        return df

    @etl_task("apply_scoring_model", "Apply scoring model to market data")
    def apply_scoring_model(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply scoring model to market data."""
        # This is a simplified scoring model - in reality this would be more complex
        # and could use ML models from the plugin registry

        # Calculate market score based on income and population
        df["market_score"] = (
            df["b19013_001e"] / df["b19013_001e"].max() * 0.4  # Income factor (40%)
            + df["b01003_001e"] / df["b01003_001e"].max() * 0.6  # Population factor (60%)
        ) * 100  # Scale to 0-100

        # Categorize markets
        df["market_tier"] = pd.cut(
            df["market_score"], bins=[0, 25, 50, 75, 100], labels=["D", "C", "B", "A"]
        )

        # Add scoring metadata
        df["scoring_model"] = "simple_income_population_v1"
        df["scored_at"] = pd.Timestamp.now()

        self.logger.info(f"Applied scoring to {len(df)} markets")
        return df

    @etl_task("store_scoring_results", "Store scoring results in data lake")
    def store_scoring_results(self, df: pd.DataFrame, as_of: str) -> str:
        """Store scoring results in data lake."""
        lake = DataLake()
        return lake.write(df, "market_scores", as_of=as_of)

    @etl_task("export_scores", "Export scores to external targets")
    def export_market_scores(self, df: pd.DataFrame, as_of: str) -> dict:
        """Export market scores to configured destinations."""
        exports = {}
        try:
            validate_data_quality(df, dataset_type="market_data")
            exports["validation"] = "ok"
        except Exception as e:
            exports["validation"] = f"failed: {e}"
        return exports


@timed_flow
@with_run_context
def score_all_markets(as_of: str = "2025-09") -> dict:
    flow = MarketScoringFlow()

    df = flow.load_market_data(as_of)
    df = flow.apply_scoring_model(df)
    partition = flow.store_scoring_results(df, as_of)
    exports = flow.export_market_scores(df, as_of)

    return {"partition": partition, **exports}


if __name__ == "__main__":
    # For local testing
    import sys

    if len(sys.argv) > 1:
        as_of = sys.argv[1]
    else:
        as_of = "2025-09"

    result = score_all_markets(as_of=as_of)
    print(f"Market scoring completed: {result}")
