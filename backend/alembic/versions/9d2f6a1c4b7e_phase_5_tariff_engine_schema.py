"""phase 5 tariff engine schema

Revision ID: 9d2f6a1c4b7e
Revises: 5a9237565b85
Create Date: 2026-09-17 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# The generic sa.Enum(..., create_type=False) does not reliably suppress
# CREATE TYPE on the postgresql dialect — the dialect-specific ENUM does
# (see the same fix in 4a3fd3105658_india_discom_tariff_and_incentive_.py).
TARIFF_CONSUMER_CATEGORY_ENUM = PGEnum(
    'RESIDENTIAL', 'COMMERCIAL', 'EDUCATIONAL_INSTITUTION', 'PUBLIC_SERVICE',
    'INDUSTRIAL', 'AGRICULTURE', 'OTHER',
    name='tariffconsumercategory', create_type=False,
)
BUILDING_TYPE_ENUM = PGEnum(
    'HOME', 'SCHOOL', 'COLLEGE', 'OFFICE', 'SHOP', 'SMALL_INSTITUTION', 'OTHER',
    name='buildingtype', create_type=False,
)


# revision identifiers, used by Alembic.
revision: str = '9d2f6a1c4b7e'
down_revision: Union[str, Sequence[str], None] = '5a9237565b85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # electricity_tariffs has zero production rows as of this migration (see
    # the model docstring) — safe to change consumer_category's type and add
    # NOT NULL columns without a backfill/default.
    TARIFF_CONSUMER_CATEGORY_ENUM.create(op.get_bind(), checkfirst=True)

    op.drop_column('electricity_tariffs', 'consumer_category')
    op.add_column(
        'electricity_tariffs',
        sa.Column('consumer_category', TARIFF_CONSUMER_CATEGORY_ENUM, nullable=False),
    )
    op.add_column(
        'electricity_tariffs',
        sa.Column('tariff_version', sa.String(length=100), nullable=False),
    )
    op.add_column(
        'electricity_tariffs',
        sa.Column('wheeling_charge_inr_per_kwh', sa.Numeric(precision=8, scale=4), nullable=True),
    )
    op.add_column(
        'electricity_tariffs',
        sa.Column('source_name', sa.String(length=255), nullable=True),
    )
    op.alter_column('electricity_tariffs', 'slab_min_kwh', nullable=False)

    op.create_table(
        'tariff_calculation_snapshots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('assessment_id', sa.Uuid(), nullable=False),
        sa.Column('calculation_version', sa.String(length=50), nullable=False),
        sa.Column('input_snapshot', sa.JSON(), nullable=False),
        sa.Column('result_snapshot', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('tariff_calculation_snapshots')

    op.alter_column('electricity_tariffs', 'slab_min_kwh', nullable=True)
    op.drop_column('electricity_tariffs', 'source_name')
    op.drop_column('electricity_tariffs', 'wheeling_charge_inr_per_kwh')
    op.drop_column('electricity_tariffs', 'tariff_version')

    op.drop_column('electricity_tariffs', 'consumer_category')
    op.add_column(
        'electricity_tariffs',
        sa.Column('consumer_category', BUILDING_TYPE_ENUM, nullable=False),
    )

    # Postgres has no "ALTER TYPE ... DROP VALUE"; tariffconsumercategory is
    # a type this migration created outright, so (unlike buildingtype's
    # 'college' label) dropping the whole type on downgrade is safe here —
    # nothing else references it.
    sa.Enum(name='tariffconsumercategory').drop(op.get_bind(), checkfirst=True)
