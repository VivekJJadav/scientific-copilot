"""add debate_history table

Revision ID: b3a7c2d4e5f6
Revises: aa8c715b5350
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "b3a7c2d4e5f6"
down_revision = "aa8c715b5350"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "debate_history",
        sa.Column("id", sa.dialects.postgresql.UUID(), primary_key=True),
        sa.Column("hypothesis_id", sa.dialects.postgresql.UUID(), sa.ForeignKey("hypotheses.id"), nullable=False, index=True),
        sa.Column("verdict", sa.String(), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("objections", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rebuttals", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("surviving_risks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("arbiter_notes", sa.Text(), nullable=True),
        sa.Column("final_novelty_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("final_feasibility_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("addressed_prior_objections", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("debate_history")
