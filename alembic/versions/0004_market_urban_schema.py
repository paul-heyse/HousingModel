"""market_urban schema for urban convenience metrics

Revision ID: 0004_market_urban_schema
Revises: 0003_materialized_schema
Create Date: 2025-09-27
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_market_urban_schema"
down_revision = "0003_materialized_schema"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bool(bind) and bind.dialect.name == "postgresql"


def upgrade() -> None:
    # Market urban convenience metrics table
    op.create_table(
        "market_urban",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("msa_id", sa.String(length=12), nullable=False),
        sa.Column("msa_name", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        # 15-minute accessibility counts (walk)
        sa.Column("walk_15_grocery_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_pharmacy_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_healthcare_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_education_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_transit_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_recreation_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_shopping_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_dining_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_banking_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_services_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("walk_15_total_ct", sa.Integer(), nullable=False, default=0),
        # 15-minute accessibility counts (bike)
        sa.Column("bike_15_grocery_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_pharmacy_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_healthcare_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_education_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_transit_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_recreation_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_shopping_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_dining_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_banking_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_services_ct", sa.Integer(), nullable=False, default=0),
        sa.Column("bike_15_total_ct", sa.Integer(), nullable=False, default=0),
        # Urban connectivity metrics
        sa.Column("interx_km2", sa.Float(), nullable=False, default=0.0),
        sa.Column("bikeway_conn_idx", sa.Float(), nullable=False, default=0.0),
        # Retail health metrics
        sa.Column("retail_vac", sa.Float(), nullable=False, default=0.0),
        sa.Column("retail_rent_qoq", sa.Float(), nullable=False, default=0.0),
        # Daytime population metrics
        sa.Column("daytime_pop_1mi", sa.Integer(), nullable=False, default=0),
        # Composite scores
        sa.Column("walk_15_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("bike_15_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("connectivity_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("retail_health_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("urban_convenience_score", sa.Float(), nullable=False, default=0.0),
        # Metadata
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("data_quality_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("run_id", sa.Integer(), nullable=True),
        # Foreign key constraints
        sa.ForeignKeyConstraint(["msa_id"], ["markets.msa_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("msa_id", "last_updated", name="uq_market_urban_msa_last_updated"),
    )

    # Indexes for performance
    op.create_index("ix_market_urban_msa_id", "market_urban", ["msa_id"])
    op.create_index("ix_market_urban_urban_score", "market_urban", ["urban_convenience_score"])
    op.create_index("ix_market_urban_last_updated", "market_urban", ["last_updated"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_market_urban_last_updated", table_name="market_urban")
    op.drop_index("ix_market_urban_urban_score", table_name="market_urban")
    op.drop_index("ix_market_urban_msa_id", table_name="market_urban")

    # Drop table
    op.drop_table("market_urban")
