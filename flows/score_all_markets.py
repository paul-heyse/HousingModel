"""Market scoring flow - scores all markets using latest data and models."""

from __future__ import annotations

import pandas as pd
from prefect import flow, task

from aker_core.config import get_settings
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
        df['market_score'] = (
            df['b19013_001e'] / df['b19013_001e'].max() * 0.4 +  # Income factor (40%)
            df['b01003_001e'] / df['b01003_001e'].max() * 0.6    # Population factor (60%)
        ) * 100  # Scale to 0-100

        # Categorize markets
        df['market_tier'] = pd.cut(
            df['market_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['D', 'C', 'B', 'A']
        )

        # Add scoring metadata
        df['scoring_model'] = 'simple_income_population_v1'
        df['scored_at'] = pd.Timestamp.now()

        self.logger.info(f"Applied scoring to {len(df)} markets")
        return df

    @etl_task("store_scoring_results", "Store scoring results in data lake")
    def store_scoring_results(self, df: pd.DataFrame, as_of: str) -> str:
        """Store scoring results in data lake."""
        lake = DataLake()

        # Store scoring results
        result_path = lake.write(
            df,
            dataset="market_scores",
            as_of=as_of,
            partition_by=["market_tier"]
        )

        self.logger.info(f"Stored market scores to {result_path}")
        return result_path

    @etl_task("export_market_scores", "Export market scores to configured destinations")
    def export_market_scores(self, df: pd.DataFrame, as_of: str) -> dict:
        """Export market scores to configured destinations."""
        settings = get_settings()
        exports = {}

        # Export to CSV file (could be S3, database, etc.)
        export_path = f"./exports/market_scores_{as_of}.csv"
        df.to_csv(export_path, index=False)
        exports["csv"] = export_path

        # Export summary statistics
        summary = {
            "total_markets": len(df),
            "avg_score": df['market_score'].mean(),
            "score_distribution": df['market_tier'].value_counts().to_dict(),
            "top_markets": df.nlargest(10, 'market_score')[['name', 'market_score', 'market_tier']].to_dict('records'),
            "exported_at": pd.Timestamp.now().isoformat(),
            "as_of": as_of
        }

        # Store summary in JSON format
        summary_path = f"./exports/market_scores_summary_{as_of}.json"
        import json
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        exports["summary_json"] = summary_path

        self.logger.info(f"Exported market scores to {len(exports)} destinations")
        return exports

    @etl_task("validate_scoring_results", "Validate scoring results quality")
    def validate_scoring_results(self, df: pd.DataFrame) -> bool:
        """Validate scoring results."""
        # Basic validation checks
        required_columns = ['name', 'market_score', 'market_tier', 'scoring_model']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if len(df) == 0:
            raise ValueError("No scoring results generated")

        # Check score ranges
        if df['market_score'].min() < 0 or df['market_score'].max() > 100:
            raise ValueError("Market scores outside valid range [0, 100]")

        # Check for reasonable distribution
        tier_counts = df['market_tier'].value_counts()
        if len(tier_counts) == 0:
            raise ValueError("No markets assigned to tiers")

        self.logger.info(f"Scoring validation passed for {len(df)} markets")
        return True


@timed_flow
@with_run_context
def score_all_markets(as_of: str = None) -> dict:
    """Score all markets using latest data and models.

    Args:
        as_of: As-of date for data partitioning (YYYY-MM format)

    Returns:
        Dictionary with export paths and summary statistics
    """
    if as_of is None:
        from datetime import datetime
        as_of = datetime.now().strftime("%Y-%m")

    flow = MarketScoringFlow()

    # Log flow start
    flow.log_start(as_of=as_of)

    try:
        # Execute scoring pipeline
        market_data = flow.load_market_data(as_of)
        scored_data = flow.apply_scoring_model(market_data)
        flow.validate_scoring_results(scored_data)
        result_path = flow.store_scoring_results(scored_data, as_of)
        exports = flow.export_market_scores(scored_data, as_of)

        flow.log_complete(
            0.0,
            markets_scored=len(scored_data),
            avg_score=scored_data['market_score'].mean(),
            as_of=as_of
        )

        return {
            "data_lake_path": result_path,
            "exports": exports,
            "summary": {
                "markets_scored": len(scored_data),
                "avg_score": scored_data['market_score'].mean(),
                "tier_distribution": scored_data['market_tier'].value_counts().to_dict()
            }
        }

    except Exception as e:
        flow.log_error(str(e), 0.0, as_of=as_of)
        raise


if __name__ == "__main__":
    # For local testing
    import sys

    if len(sys.argv) > 1:
        as_of = sys.argv[1]
    else:
        as_of = None

    result = score_all_markets(as_of=as_of)
    print(f"Market scoring completed: {result}")
