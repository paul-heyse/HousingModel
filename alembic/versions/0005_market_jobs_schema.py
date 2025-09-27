"""market jobs schema

Revision ID: 0005_market_jobs_schema
Revises: 0004_supply_calculators
Create Date: 2025-09-27
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_market_jobs_schema"
down_revision = ("0004_supply_calculators", "0004_market_urban_schema")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_jobs",
        sa.Column("sba_id", sa.String(length=24), primary_key=True),
        sa.Column(
            "msa_id",
            sa.String(length=12),
            sa.ForeignKey("markets.msa_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("data_vintage", sa.String(length=20), nullable=True),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("source_data_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("runs.run_id", ondelete="SET NULL"), nullable=True
        ),
        # Location quotient metrics
        sa.Column("tech_lq", sa.Float(), nullable=True),
        sa.Column("health_lq", sa.Float(), nullable=True),
        sa.Column("education_lq", sa.Float(), nullable=True),
        sa.Column("manufacturing_lq", sa.Float(), nullable=True),
        sa.Column("defense_lq", sa.Float(), nullable=True),
        sa.Column("biotech_lq", sa.Float(), nullable=True),
        # CAGR metrics (1yr/3yr/5yr)
        sa.Column("tech_cagr_1yr", sa.Float(), nullable=True),
        sa.Column("tech_cagr_3yr", sa.Float(), nullable=True),
        sa.Column("tech_cagr_5yr", sa.Float(), nullable=True),
        sa.Column("health_cagr_1yr", sa.Float(), nullable=True),
        sa.Column("health_cagr_3yr", sa.Float(), nullable=True),
        sa.Column("health_cagr_5yr", sa.Float(), nullable=True),
        sa.Column("education_cagr_3yr", sa.Float(), nullable=True),
        sa.Column("education_cagr_5yr", sa.Float(), nullable=True),
        sa.Column("manufacturing_cagr_3yr", sa.Float(), nullable=True),
        sa.Column("manufacturing_cagr_5yr", sa.Float(), nullable=True),
        # Awards per 100k population
        sa.Column("nih_awards_per_100k", sa.Float(), nullable=True),
        sa.Column("nsf_awards_per_100k", sa.Float(), nullable=True),
        sa.Column("dod_awards_per_100k", sa.Float(), nullable=True),
        sa.Column("total_awards_per_100k", sa.Float(), nullable=True),
        # Business formation and survival metrics
        sa.Column("bfs_applications_per_100k", sa.Float(), nullable=True),
        sa.Column("bfs_high_propensity_per_100k", sa.Float(), nullable=True),
        sa.Column("startup_density", sa.Float(), nullable=True),
        sa.Column("business_survival_1yr", sa.Float(), nullable=True),
        sa.Column("business_survival_5yr", sa.Float(), nullable=True),
        # Migration & labour market metrics
        sa.Column("mig_25_44_per_1k", sa.Float(), nullable=True),
        sa.Column("unemployment_rate", sa.Float(), nullable=True),
        sa.Column("labor_participation_rate", sa.Float(), nullable=True),
        sa.Column("knowledge_jobs_share", sa.Float(), nullable=True),
        # Expansion tracking summary
        sa.Column("expansions_total_ct", sa.Integer(), nullable=True),
        sa.Column("expansions_total_jobs", sa.Integer(), nullable=True),
        sa.Column("expansions_university_ct", sa.Integer(), nullable=True),
        sa.Column("expansions_university_jobs", sa.Integer(), nullable=True),
        sa.Column("expansions_health_ct", sa.Integer(), nullable=True),
        sa.Column("expansions_health_jobs", sa.Integer(), nullable=True),
        sa.Column("expansions_semiconductor_ct", sa.Integer(), nullable=True),
        sa.Column("expansions_semiconductor_jobs", sa.Integer(), nullable=True),
        sa.Column("expansions_defense_ct", sa.Integer(), nullable=True),
        sa.Column("expansions_defense_jobs", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "tech_lq IS NULL OR tech_lq >= 0", name="ck_market_jobs_tech_lq_positive"
        ),
        sa.CheckConstraint(
            "health_lq IS NULL OR health_lq >= 0", name="ck_market_jobs_health_lq_positive"
        ),
        sa.CheckConstraint(
            "total_awards_per_100k IS NULL OR total_awards_per_100k >= 0",
            name="ck_market_jobs_awards_positive",
        ),
        sa.CheckConstraint(
            "unemployment_rate IS NULL OR (unemployment_rate >= 0 AND unemployment_rate <= 100)",
            name="ck_market_jobs_unemployment_range",
        ),
        sa.CheckConstraint(
            "labor_participation_rate IS NULL OR (labor_participation_rate >= 0 AND labor_participation_rate <= 100)",
            name="ck_market_jobs_lfp_range",
        ),
        sa.CheckConstraint(
            "knowledge_jobs_share IS NULL OR (knowledge_jobs_share >= 0 AND knowledge_jobs_share <= 100)",
            name="ck_market_jobs_knowledge_share",
        ),
    )

    op.create_index(
        "ix_market_jobs_msa_vintage",
        "market_jobs",
        ["msa_id", "data_vintage"],
    )
    op.create_index(
        "ix_market_jobs_expansions_total",
        "market_jobs",
        ["expansions_total_ct"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_jobs_expansions_total", table_name="market_jobs")
    op.drop_index("ix_market_jobs_msa_vintage", table_name="market_jobs")
    op.drop_table("market_jobs")
