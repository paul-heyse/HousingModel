"""materialized analytics tables and views

Revision ID: 0003_materialized_schema
Revises: 0002_extra_tables
Create Date: 2025-09-26
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_materialized_schema"
down_revision = "0002_extra_tables"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bool(bind) and bind.dialect.name == "postgresql"


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    if not bind:
        return False
    inspector = sa.inspect(bind)
    try:
        return inspector.has_table(table_name)
    except Exception:
        return False


def upgrade() -> None:
    is_postgres = _is_postgres()
    # Materialized analytics table
    op.create_table(
        "market_analytics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("msa_id", sa.String(length=12), nullable=False),
        sa.Column("market_name", sa.String(length=120), nullable=False),
        sa.Column("period_month", sa.Date(), nullable=False),
        sa.Column("supply_score", sa.Float(), nullable=True),
        sa.Column("jobs_score", sa.Float(), nullable=True),
        sa.Column("urban_score", sa.Float(), nullable=True),
        sa.Column("outdoor_score", sa.Float(), nullable=True),
        sa.Column("composite_score", sa.Float(), nullable=True),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("households", sa.Integer(), nullable=True),
        sa.Column("vacancy_rate", sa.Float(), nullable=True),
        sa.Column("permit_per_1k", sa.Float(), nullable=True),
        sa.Column("tech_cagr", sa.Float(), nullable=True),
        sa.Column(
            "refreshed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["msa_id"], ["markets.msa_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_market_analytics_msa_period",
        "market_analytics",
        ["msa_id", "period_month"],
        unique=True,
    )
    op.create_index("ix_market_analytics_composite", "market_analytics", ["composite_score"])

    # Asset performance materialized table
    op.create_table(
        "asset_performance",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("msa_id", sa.String(length=12), nullable=False),
        sa.Column("period_month", sa.Date(), nullable=False),
        sa.Column("units", sa.Integer(), nullable=True),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("market_composite_score", sa.Float(), nullable=True),
        sa.Column("rank_in_market", sa.Integer(), nullable=True),
        sa.Column(
            "refreshed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.asset_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["msa_id"], ["markets.msa_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_asset_performance_asset_period",
        "asset_performance",
        ["asset_id", "period_month"],
        unique=True,
    )
    op.create_index("ix_asset_performance_score", "asset_performance", ["score"])

    # Add foreign keys for existing tables
    if is_postgres:
        op.create_foreign_key(
            "fk_pillar_scores_msa_id_markets",
            "pillar_scores",
            "markets",
            ["msa_id"],
            ["msa_id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            "fk_pillar_scores_run_id_runs",
            "pillar_scores",
            "runs",
            ["run_id"],
            ["run_id"],
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            "fk_assets_msa_id_markets",
            "assets",
            "markets",
            ["msa_id"],
            ["msa_id"],
            ondelete="CASCADE",
        )

    for table in ("market_supply", "market_jobs", "market_urban", "market_outdoors"):
        if not _table_exists(table):
            continue
        op.add_column(table, sa.Column("msa_id", sa.String(length=12), nullable=True))
        if is_postgres:
            op.create_foreign_key(
                f"fk_{table}_msa_id_markets",
                table,
                "markets",
                ["msa_id"],
                ["msa_id"],
                ondelete="CASCADE",
            )
        op.create_index(f"ix_{table}_msa_id", table, ["msa_id"])

    # Spatial and composite indexes (Postgres only)
    if is_postgres:
        op.execute("CREATE INDEX IF NOT EXISTS ix_markets_geo_gist ON markets USING GIST (geo)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_assets_geo_gist ON assets USING GIST (geo)")
    else:
        # Fallback simple indexes for SQLite or other engines on the geometry text column
        op.create_index("ix_markets_geo", "markets", ["geo"])
        op.create_index("ix_assets_geo", "assets", ["geo"])

    # Views for complex joins
    op.execute(
        """
        CREATE VIEW market_supply_joined AS
        SELECT
            m.msa_id,
            m.name AS market_name,
            ms.sba_id,
            ms.msa_id AS supply_msa_id,
            ms.permit_per_1k,
            ms.vacancy_rate,
            mj.tech_cagr,
            mu.walk_15_ct,
            mo.trail_mi_pc,
            ma.composite_score,
            ma.period_month
        FROM markets m
        LEFT JOIN market_supply ms ON ms.msa_id = m.msa_id
        LEFT JOIN market_jobs mj ON mj.msa_id = m.msa_id
        LEFT JOIN market_urban mu ON mu.msa_id = m.msa_id
        LEFT JOIN market_outdoors mo ON mo.msa_id = m.msa_id
        LEFT JOIN market_analytics ma ON ma.msa_id = m.msa_id;
        """
    )

    op.execute(
        """
        CREATE VIEW asset_scoring_joined AS
        SELECT
            a.asset_id,
            a.msa_id,
            a.units,
            a.year_built,
            ap.period_month,
            ap.score,
            ap.market_composite_score,
            ap.rank_in_market,
            ap.run_id AS analytics_run_id,
            ps.weighted_0_5,
            ps.weighted_0_100,
            ps.score_as_of,
            ps.weights,
            ps.run_id AS score_run_id
        FROM assets a
        LEFT JOIN asset_performance ap ON ap.asset_id = a.asset_id
        LEFT JOIN pillar_scores ps ON ps.msa_id = a.msa_id;
        """
    )


def downgrade() -> None:
    is_postgres = _is_postgres()
    op.execute("DROP VIEW IF EXISTS asset_scoring_joined")
    op.execute("DROP VIEW IF EXISTS market_supply_joined")

    if is_postgres:
        op.execute("DROP INDEX IF EXISTS ix_markets_geo_gist")
        op.execute("DROP INDEX IF EXISTS ix_assets_geo_gist")
    else:
        op.drop_index("ix_markets_geo", table_name="markets")
        op.drop_index("ix_assets_geo", table_name="assets")

    for table in ("market_supply", "market_jobs", "market_urban", "market_outdoors"):
        if not _table_exists(table):
            continue
        op.drop_index(f"ix_{table}_msa_id", table_name=table)
        if is_postgres:
            op.drop_constraint(f"fk_{table}_msa_id_markets", table_name=table, type_="foreignkey")
        op.drop_column(table, "msa_id")

    if is_postgres:
        op.drop_constraint("fk_assets_msa_id_markets", "assets", type_="foreignkey")
        op.drop_constraint("fk_pillar_scores_run_id_runs", "pillar_scores", type_="foreignkey")
        op.drop_constraint("fk_pillar_scores_msa_id_markets", "pillar_scores", type_="foreignkey")

    op.drop_index("ix_asset_performance_score", table_name="asset_performance")
    op.drop_index("ix_asset_performance_asset_period", table_name="asset_performance")
    op.drop_table("asset_performance")

    op.drop_index("ix_market_analytics_composite", table_name="market_analytics")
    op.drop_index("ix_market_analytics_msa_period", table_name="market_analytics")
    op.drop_table("market_analytics")
