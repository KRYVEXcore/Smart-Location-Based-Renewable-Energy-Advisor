import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)


class IncentiveProgram(Base):
    """A single central, state/UT, or DISCOM renewable-energy incentive
    scheme — one row per scheme *version* (unlike ElectricityTariff, where
    one row is one slab; an incentive program is inherently one coherent
    set of rules, not a bracket of a larger schedule).

    `scheme_version` groups the historical versions of what is
    conceptually "the same scheme" (matched by scheme_name + level +
    technology — see app.engines.incentive.version_selection) so an old
    version is never overwritten, and the correct one is selected by
    effective date.

    `consumer_category` reuses Phase 5's TariffConsumerCategory (see
    app.engines.tariff.consumer_category_mapping) rather than BuildingType
    directly — Phase 6 must not create a second, incompatible category
    mapping. NULL means genuinely category-agnostic; the eligibility
    engine must never treat NULL as "applies to everyone" without also
    checking `eligibility_rules`.

    `verification_status` is distinct from `active`: only VERIFIED rows
    are used for automatic eligibility/calculation (see
    app.engines.incentive.eligibility) — a PENDING_REVIEW/UNAVAILABLE row
    can still be recorded (for the research record) without ever being
    presented as a real, applicable subsidy.

    Rows are only ever loaded from backend/app/data/incentives/india/ by
    scripts/seed_incentives.py, after being validated against an official
    source (see app.data_validation). See that folder's README.md for the
    per-scheme investigation record.
    """

    __tablename__ = "incentive_programs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scheme_version: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[IncentiveLevel] = mapped_column(Enum(IncentiveLevel), nullable=False)
    incentive_type: Mapped[IncentiveType] = mapped_column(Enum(IncentiveType), nullable=False)

    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    union_territory: Mapped[str | None] = mapped_column(String(120), nullable=True)
    discom_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("discoms.id"), nullable=True)
    consumer_category: Mapped[TariffConsumerCategory | None] = mapped_column(
        Enum(TariffConsumerCategory), nullable=True
    )
    technology: Mapped[RenewableTechnology] = mapped_column(Enum(RenewableTechnology), nullable=False)

    min_system_size_kw: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    max_system_size_kw: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)

    subsidy_type: Mapped[SubsidyType] = mapped_column(Enum(SubsidyType), nullable=False)
    # Generic amount whose meaning depends on subsidy_type (e.g. INR per kW
    # for PER_KW, a flat INR amount for FIXED_AMOUNT).
    subsidy_value: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Specific to PERCENTAGE-type subsidies. Requires a real eligible cost
    # basis to calculate, which this app does not collect — see
    # app.engines.incentive.calculator (always "insufficient_information"
    # for PERCENTAGE/BENCHMARK_COST_BASED today).
    percentage_value: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    # A cap applicable to PERCENTAGE, PER_KW, SLAB_BASED, or
    # BENCHMARK_COST_BASED amounts alike — never to FIXED_AMOUNT (already a
    # single fixed number).
    maximum_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Structured formula inputs for SLAB_BASED (a "slabs" list keyed by
    # capacity_min_kw/capacity_max_kw/rate_inr_per_kw) and
    # BENCHMARK_COST_BASED (benchmark_cost_per_kw_inr + eligible_percentage)
    # calculation types — see app.engines.incentive.calculator for the
    # exact schema each type expects.
    calculation_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Generic conditions the eligibility engine checks against whatever
    # assessment context is actually available — see
    # app.engines.incentive.eligibility. A condition referencing a field
    # this app never collects always resolves as missing, never guessed.
    eligibility_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    application_requirements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Combinability with other programmes — see
    # app.engines.incentive.stacking. Absent/incomplete rules mean
    # "unverified", never "combinable by default".
    stacking_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_status: Mapped[IncentiveVerificationStatus] = mapped_column(
        Enum(IncentiveVerificationStatus), nullable=False
    )
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_order_number: Mapped[str | None] = mapped_column(String(160), nullable=True)
    source_order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_page: Mapped[str | None] = mapped_column(String(160), nullable=True)
    source_table: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
