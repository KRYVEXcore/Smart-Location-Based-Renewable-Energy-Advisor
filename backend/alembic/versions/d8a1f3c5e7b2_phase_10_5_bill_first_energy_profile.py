"""phase 10.5 bill-first energy profile

Revision ID: d8a1f3c5e7b2
Revises: c7d2e9f4a6b1
Create Date: 2026-09-20 12:00:00.000000

Backward compatible: existing rows keep their monthly_consumption_kwh and are marked
'user_kwh'. monthly_consumption_kwh becomes nullable (NULL = a bill estimate could not be
made); nothing is dropped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd8a1f3c5e7b2'
down_revision: Union[str, Sequence[str], None] = 'c7d2e9f4a6b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('energy_profiles', sa.Column('monthly_electricity_bill_inr', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('energy_profiles', sa.Column('consumption_source', sa.String(length=30), server_default='user_kwh', nullable=False))
    op.add_column('energy_profiles', sa.Column('consumption_estimate', sa.JSON(), nullable=True))
    op.alter_column('energy_profiles', 'monthly_consumption_kwh', existing_type=sa.Numeric(precision=10, scale=2), nullable=True)


def downgrade() -> None:
    # Fails on purpose if any bill-first row has no kWh value: nothing is deleted or invented.
    op.alter_column('energy_profiles', 'monthly_consumption_kwh', existing_type=sa.Numeric(precision=10, scale=2), nullable=False)
    op.drop_column('energy_profiles', 'consumption_estimate')
    op.drop_column('energy_profiles', 'consumption_source')
    op.drop_column('energy_profiles', 'monthly_electricity_bill_inr')
