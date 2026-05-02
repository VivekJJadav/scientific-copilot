"""Add pipeline_tasks table

Revision ID: 2f4f6d7a8b9c
Revises: f8e5f67bf3a1
Create Date: 2026-04-17 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql


revision: str = "2f4f6d7a8b9c"
down_revision: Union[str, None] = "f8e5f67bf3a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_tasks",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("step", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("history", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pipeline_tasks_status"), "pipeline_tasks", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pipeline_tasks_status"), table_name="pipeline_tasks")
    op.drop_table("pipeline_tasks")
