import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models.enums import BuildingType, IncentiveLevel, RenewableTechnology, SubsidyType


class IncentiveProgram(Base):
    """A single central, state/UT, or DISCOM incentive scheme.

    `consumer_category` is nullable to allow a genuinely category-agnostic
    scheme, but a future matching engine must treat NULL as "verify
    eligibility_rules" — never as "applies to everyone". This is exactly
    the rule that stops a residential central subsidy (e.g. PM Surya Ghar)
    from being silently applied to a school or office; each of those needs
    its own explicit row (or an explicit NULL + rule) once verified.

    No production rows are seeded by this migration — populating real
    schemes is future work; this only prepares the schema.
    """

    __tablename__ = "incentive_programs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[IncentiveLevel] = mapped_column(Enum(IncentiveLevel), nullable=False)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    union_territory: Mapped[str | None] = mapped_column(String(120), nullable=True)
    discom_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("discoms.id"), nullable=True)
    consumer_category: Mapped[BuildingType | None] = mapped_column(Enum(BuildingType), nullable=True)
    technology: Mapped[RenewableTechnology] = mapped_column(Enum(RenewableTechnology), nullable=False)

    min_system_size_kw: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    max_system_size_kw: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)

    subsidy_type: Mapped[SubsidyType] = mapped_column(Enum(SubsidyType), nullable=False)
    # Generic amount whose meaning depends on subsidy_type (e.g. INR per kW
    # for PER_KW, a flat INR amount for FIXED_AMOUNT).
    subsidy_value: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Specific to PERCENTAGE-type subsidies, optionally capped by maximum_amount.
    percentage_value: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    maximum_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    eligibility_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
