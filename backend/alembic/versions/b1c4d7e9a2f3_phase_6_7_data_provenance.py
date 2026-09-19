"""phase 6.7 data provenance columns

Revision ID: b1c4d7e9a2f3
Revises: 3e7c8a2f5d91
Create Date: 2026-09-19 09:00:00.000000

Adds explicit source provenance (order number/date, page, table, section,
excerpt, notes) to tariffs and incentives, a verification status and fixed
charge basis to tariffs. Additive only: no existing column is changed or
dropped and no row is rewritten.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# The type already exists (created in 3e7c8a2f5d91); create_type=False so
# adding a column that uses it never tries to create it again.
INCENTIVE_VERIFICATION_STATUS_ENUM = PGEnum(
    'VERIFIED', 'PENDING_REVIEW', 'EXPIRED', 'SUPERSEDED', 'UNAVAILABLE',
    name='incentiveverificationstatus', create_type=False,
)

revision: str = 'b1c4d7e9a2f3'
down_revision: Union[str, Sequence[str], None] = '3e7c8a2f5d91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PROVENANCE_COLUMNS = (
    ('source_order_number', sa.String(160)),
    ('source_order_date', sa.Date()),
    ('source_page', sa.String(160)),
    ('source_table', sa.String(255)),
    ('source_section', sa.String(255)),
    ('source_excerpt', sa.Text()),
    ('verification_notes', sa.Text()),
)


def upgrade() -> None:
    for table in ('electricity_tariffs', 'incentive_programs'):
        for name, column_type in PROVENANCE_COLUMNS:
            op.add_column(table, sa.Column(name, column_type, nullable=True))

    op.add_column('electricity_tariffs', sa.Column('fixed_charge_basis', sa.String(40), nullable=True))
    # Any pre-existing tariff row (none in production) stays untrusted until
    # explicitly verified: the server default is PENDING_REVIEW, never VERIFIED.
    op.add_column(
        'electricity_tariffs',
        sa.Column(
            'verification_status',
            INCENTIVE_VERIFICATION_STATUS_ENUM,
            nullable=False,
            server_default='PENDING_REVIEW',
        ),
    )


def downgrade() -> None:
    op.drop_column('electricity_tariffs', 'verification_status')
    op.drop_column('electricity_tariffs', 'fixed_charge_basis')
    for table in ('incentive_programs', 'electricity_tariffs'):
        for name, _ in reversed(PROVENANCE_COLUMNS):
            op.drop_column(table, name)
