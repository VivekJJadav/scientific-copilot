"""Add hypotheses table

Revision ID: 0002
Revises: 0001
Create Date: 2024-05-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('hypotheses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('motivation', sa.Text(), nullable=False),
        sa.Column('core_claim', sa.Text(), nullable=False),
        sa.Column('method_sketch', sa.Text(), nullable=False),
        sa.Column('expected_outcome', sa.Text(), nullable=False),
        sa.Column('risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('novelty_score', sa.Float(), nullable=False),
        sa.Column('feasibility_score', sa.Float(), nullable=False),
        sa.Column('hardware_requirement', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('source_paper_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('gap_description', sa.Text(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('iteration_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('hypotheses')
