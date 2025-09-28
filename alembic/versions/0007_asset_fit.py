"""asset fit table

Revision ID: 0007_asset_fit
Revises: 0006_risk_profile
Create Date: 2025-10-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_asset_fit"
down_revision = "0006_risk_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS asset_fit"))

    op.create_table(
        "asset_fit",
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.asset_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("msa_id", sa.String(length=12), sa.ForeignKey("markets.msa_id", ondelete="CASCADE")),
        sa.Column("product_type", sa.String(length=40), nullable=True),
        sa.Column("context_label", sa.String(length=40), nullable=True),
        sa.Column("fit_score", sa.Float(), nullable=True),
        sa.Column("flags", sa.JSON(), nullable=True),
        sa.Column("inputs", sa.JSON(), nullable=True),
        sa.Column("ruleset_version", sa.String(length=20), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.run_id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("fit_score IS NULL OR (fit_score >= 0 AND fit_score <= 100)", name="ck_asset_fit_score_range"),
    )
    op.create_index("ix_asset_fit_msa_id", "asset_fit", ["msa_id"])
    op.create_index("ix_asset_fit_run_id", "asset_fit", ["run_id"])
    op.create_index("ix_asset_fit_fit_score", "asset_fit", ["fit_score"])


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_asset_fit_fit_score"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_asset_fit_run_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_asset_fit_msa_id"))
    op.execute(sa.text("DROP TABLE IF EXISTS asset_fit"))
