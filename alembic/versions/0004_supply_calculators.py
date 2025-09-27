"""supply constraint calculators

Revision ID: 0004_supply_calculators
Revises: 0003_materialized_schema
Create Date: 2025-09-27

Adds market_supply table with fields for elasticity, vacancy, and lease-up metrics.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_supply_calculators"
down_revision = "0003_materialized_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create market_supply table
    op.create_table(
        "market_supply",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("msa_id", sa.String(length=12), nullable=False, index=True),
        sa.Column("data_vintage", sa.String(length=20), nullable=False),
        sa.Column(
            "calculation_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Elasticity metrics
        sa.Column("elasticity_idx", sa.Float(), nullable=True),  # permits per 1k households
        sa.Column("elasticity_years", sa.Integer(), nullable=True),  # averaging period
        sa.Column("elasticity_run_id", sa.Integer(), nullable=True),  # source run
        # Vacancy metrics
        sa.Column("vacancy_rate", sa.Float(), nullable=True),  # 0-100 percentage
        sa.Column("vacancy_type", sa.String(length=20), nullable=True),  # rental, multifamily, etc
        sa.Column("vacancy_source", sa.String(length=50), nullable=True),  # HUD, local, etc
        sa.Column("vacancy_run_id", sa.Integer(), nullable=True),
        # Lease-up metrics
        sa.Column("leaseup_tom_days", sa.Float(), nullable=True),  # median days on market
        sa.Column("leaseup_sample_size", sa.Integer(), nullable=True),  # number of leases analyzed
        sa.Column("leaseup_time_window_days", sa.Integer(), nullable=True),  # analysis window
        sa.Column("leaseup_run_id", sa.Integer(), nullable=True),
        # Metadata
        sa.Column("source_data_hash", sa.String(length=64), nullable=True),
        sa.Column("calculation_version", sa.String(length=20), nullable=True),
        sa.CheckConstraint(
            "elasticity_idx IS NULL OR elasticity_idx >= 0",
            name="check_elasticity_positive",
        ),
        sa.CheckConstraint(
            "vacancy_rate IS NULL OR (vacancy_rate >= 0 AND vacancy_rate <= 100)",
            name="check_vacancy_range",
        ),
        sa.CheckConstraint(
            "leaseup_tom_days IS NULL OR leaseup_tom_days >= 0",
            name="check_leaseup_positive",
        ),
        # Foreign keys
        sa.ForeignKeyConstraint(["msa_id"], ["markets.msa_id"], ondelete="CASCADE"),
    )

    # Create indexes for performance
    op.create_index("ix_market_supply_msa_vintage", "market_supply", ["msa_id", "data_vintage"])
    op.create_index("ix_market_supply_elasticity", "market_supply", ["elasticity_idx"])
    op.create_index("ix_market_supply_vacancy", "market_supply", ["vacancy_rate"])
    op.create_index("ix_market_supply_leaseup", "market_supply", ["leaseup_tom_days"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_market_supply_leaseup", table_name="market_supply")
    op.drop_index("ix_market_supply_vacancy", table_name="market_supply")
    op.drop_index("ix_market_supply_elasticity", table_name="market_supply")
    op.drop_index("ix_market_supply_msa_vintage", table_name="market_supply")

    # Drop table
    op.drop_table("market_supply")
