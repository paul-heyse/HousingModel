from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from aker_core import OpsRepository, pricing_rules, reputation_index
from aker_data.models import Assets


def run_ops_etl(db_url: str) -> int:
    engine = create_engine(db_url)
    processed = 0
    with Session(engine) as session:
        asset_ids = [row[0] for row in session.execute(select(Assets.asset_id)).all()]
        for aid in asset_ids:
            # Placeholder: pull reviews/NPS from your connectors; here use defaults
            reviews = [{"rating": 4.2}, {"rating": 4.8, "weight": 1.5}]
            nps = 25
            idx = reputation_index(reviews, nps)
            rules = pricing_rules(idx)
            OpsRepository(session).upsert_index(
                asset_id=aid,
                nps=int(nps),
                reputation_idx=idx,
            )
            processed += 1
        session.commit()
    return processed


if __name__ == "__main__":  # pragma: no cover
    import os
    url = os.environ.get("DATABASE_URL", "sqlite+pysqlite:///ops_demo.db")
    count = run_ops_etl(url)
    print(f"Processed {count} assets")
