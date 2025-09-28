"""risk profile table

Revision ID: 0006_risk_profile
Revises: 0005_market_jobs_schema
Create Date: 2025-10-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_risk_profile"
down_revision = "0005_market_jobs_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS risk_profile"))

    op.create_table(
        "risk_profile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subject_type", sa.String(length=20), nullable=False),
        sa.Column("subject_id", sa.String(length=64), nullable=False),
        sa.Column("peril", sa.String(length=40), nullable=False),
        sa.Column("severity_idx", sa.Float(), nullable=False),
        sa.Column("multiplier", sa.Float(), nullable=False),
        sa.Column("deductible", sa.JSON(), nullable=True),
        sa.Column("data_vintage", sa.String(length=20), nullable=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("runs.run_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("calculation_method", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "severity_idx >= 0 AND severity_idx <= 100",
            name="ck_risk_profile_severity_range",
        ),
        sa.CheckConstraint(
            "multiplier >= 0.9 AND multiplier <= 1.1",
            name="ck_risk_profile_multiplier_range",
        ),
        sa.UniqueConstraint(
            "subject_type", "subject_id", "peril", name="uq_risk_profile_subject_peril"
        ),
    )
    op.create_index(
        "ix_risk_profile_subject",
        "risk_profile",
        ["subject_type", "subject_id"],
    )
    op.create_index(
        "ix_risk_profile_peril",
        "risk_profile",
        ["peril"],
    )
    op.create_index(
        "ix_risk_profile_run_id",
        "risk_profile",
        ["run_id"],
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_risk_profile_run_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_risk_profile_peril"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_risk_profile_subject"))
    op.execute(sa.text("DROP TABLE IF EXISTS risk_profile"))
