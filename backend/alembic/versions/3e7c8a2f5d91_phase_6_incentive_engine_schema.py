"""phase 6 incentive engine schema

Revision ID: 3e7c8a2f5d91
Revises: 9d2f6a1c4b7e
Create Date: 2026-09-17 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# The generic sa.Enum(..., create_type=False) does not reliably suppress
# CREATE TYPE on the postgresql dialect — the dialect-specific ENUM does
# (see the same fix in 4a3fd3105658_india_discom_tariff_and_incentive_.py
# and 9d2f6a1c4b7e_phase_5_tariff_engine_schema.py).
TARIFF_CONSUMER_CATEGORY_ENUM = PGEnum(
    'RESIDENTIAL', 'COMMERCIAL', 'EDUCATIONAL_INSTITUTION', 'PUBLIC_SERVICE',
    'INDUSTRIAL', 'AGRICULTURE', 'OTHER',
    name='tariffconsumercategory', create_type=False,
)
BUILDING_TYPE_ENUM = PGEnum(
    'HOME', 'SCHOOL', 'COLLEGE', 'OFFICE', 'SHOP', 'SMALL_INSTITUTION', 'OTHER',
    name='buildingtype', create_type=False,
)
INCENTIVE_TYPE_ENUM = PGEnum(
    'CAPITAL_SUBSIDY', 'CENTRAL_FINANCIAL_ASSISTANCE', 'STATE_SUBSIDY', 'DISCOM_INCENTIVE',
    'REBATE', 'INTEREST_SUBVENTION', 'GRANT', 'PERFORMANCE_INCENTIVE', 'OTHER',
    name='incentivetype', create_type=False,
)
INCENTIVE_VERIFICATION_STATUS_ENUM = PGEnum(
    'VERIFIED', 'PENDING_REVIEW', 'EXPIRED', 'SUPERSEDED', 'UNAVAILABLE',
    name='incentiveverificationstatus', create_type=False,
)


# revision identifiers, used by Alembic.
revision: str = '3e7c8a2f5d91'
down_revision: Union[str, Sequence[str], None] = '9d2f6a1c4b7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # incentive_programs has zero production rows as of this migration (see
    # the model docstring) — safe to change consumer_category's type and add
    # NOT NULL columns without a backfill/default.

    # New calculation-method values (see app.engines.incentive.calculator).
    # Safe within this transaction since PG 12+ — nothing here inserts a row
    # using the new values in the same transaction they're added in.
    op.execute("ALTER TYPE subsidytype ADD VALUE IF NOT EXISTS 'SLAB_BASED'")
    op.execute("ALTER TYPE subsidytype ADD VALUE IF NOT EXISTS 'BENCHMARK_COST_BASED'")

    INCENTIVE_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    INCENTIVE_VERIFICATION_STATUS_ENUM.create(op.get_bind(), checkfirst=True)

    op.drop_column('incentive_programs', 'consumer_category')
    op.add_column(
        'incentive_programs',
        sa.Column('consumer_category', TARIFF_CONSUMER_CATEGORY_ENUM, nullable=True),
    )

    op.add_column('incentive_programs', sa.Column('scheme_version', sa.String(length=100), nullable=False))
    op.add_column('incentive_programs', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('incentive_programs', sa.Column('incentive_type', INCENTIVE_TYPE_ENUM, nullable=False))
    op.add_column('incentive_programs', sa.Column('calculation_rules', sa.JSON(), nullable=True))
    op.add_column('incentive_programs', sa.Column('application_requirements', sa.JSON(), nullable=True))
    op.add_column('incentive_programs', sa.Column('stacking_rules', sa.JSON(), nullable=True))
    op.add_column(
        'incentive_programs',
        sa.Column('verification_status', INCENTIVE_VERIFICATION_STATUS_ENUM, nullable=False),
    )
    op.add_column('incentive_programs', sa.Column('source_name', sa.String(length=255), nullable=True))

    op.create_table(
        'incentive_evaluation_snapshots',
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
    op.drop_table('incentive_evaluation_snapshots')

    op.drop_column('incentive_programs', 'source_name')
    op.drop_column('incentive_programs', 'verification_status')
    op.drop_column('incentive_programs', 'stacking_rules')
    op.drop_column('incentive_programs', 'application_requirements')
    op.drop_column('incentive_programs', 'calculation_rules')
    op.drop_column('incentive_programs', 'incentive_type')
    op.drop_column('incentive_programs', 'description')
    op.drop_column('incentive_programs', 'scheme_version')

    op.drop_column('incentive_programs', 'consumer_category')
    op.add_column(
        'incentive_programs',
        sa.Column('consumer_category', BUILDING_TYPE_ENUM, nullable=True),
    )

    # Both enum types were created outright by this migration, so (unlike
    # buildingtype's 'college' label) dropping them on downgrade is safe —
    # nothing else references them.
    sa.Enum(name='incentiveverificationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='incentivetype').drop(op.get_bind(), checkfirst=True)

    # Postgres has no "ALTER TYPE ... DROP VALUE" — the subsidytype value
    # additions above are intentionally one-way, same precedent as the
    # buildingtype 'college' addition in 4a3fd3105658.
