"""Add experiments table and debate fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to hypotheses table
    op.add_column('hypotheses', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('hypotheses', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('hypotheses', sa.Column('debate_rounds', sa.Integer(), nullable=True))
    op.add_column('hypotheses', sa.Column('arbiter_notes', sa.Text(), nullable=True))

    # Create experiments table
    op.create_table('experiments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('hypothesis_id', sa.Uuid(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), server_default='queued', nullable=False),
        sa.Column('experiment_dir', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('container_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('wandb_run_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('mlflow_run_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['hypothesis_id'], ['hypotheses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('experiments')
    op.drop_column('hypotheses', 'arbiter_notes')
    op.drop_column('hypotheses', 'debate_rounds')
    op.drop_column('hypotheses', 'rejection_reason')
    op.drop_column('hypotheses', 'approved_at')
