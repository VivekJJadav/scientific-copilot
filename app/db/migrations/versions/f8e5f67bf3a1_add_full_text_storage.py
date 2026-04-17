"""Add full text storage for papers

Revision ID: f8e5f67bf3a1
Revises: ce24b4289684
Create Date: 2026-04-16 01:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f8e5f67bf3a1"
down_revision = "ce24b4289684"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("papers", sa.Column("full_text", sa.Text(), nullable=True))
    op.add_column("papers", sa.Column("text_chunks", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("papers", sa.Column("content_source", sa.Text(), nullable=False, server_default="abstract"))


def downgrade() -> None:
    op.drop_column("papers", "content_source")
    op.drop_column("papers", "text_chunks")
    op.drop_column("papers", "full_text")
