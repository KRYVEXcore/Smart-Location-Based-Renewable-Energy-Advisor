"""phase 7 wind calculation snapshots

Revision ID: c7d2e9f4a6b1
Revises: b1c4d7e9a2f3
Create Date: 2026-09-19 12:00:00.000000

Additive only: one new audit table, same shape as solar_calculation_snapshots.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c7d2e9f4a6b1'
down_revision: Union[str, Sequence[str], None] = 'b1c4d7e9a2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('wind_calculation_snapshots',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('assessment_id', sa.Uuid(), nullable=False),
    sa.Column('calculation_version', sa.String(length=50), nullable=False),
    sa.Column('assumption_version', sa.String(length=50), nullable=False),
    sa.Column('input_snapshot', sa.JSON(), nullable=False),
    sa.Column('result_snapshot', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('wind_calculation_snapshots')
