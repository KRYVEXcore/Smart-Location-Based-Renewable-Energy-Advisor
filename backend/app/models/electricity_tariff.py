import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models.enums import IncentiveVerificationStatus, TariffConsumerCategory


class ElectricityTariff(Base):
    """A single tariff slab, scoped to a state/UT, optionally a DISCOM, and a
    consumer category. Real tariff orders are published as several slabs
    (e.g. 0-100 kWh, 101-300 kWh, ...) — one row per slab.

    `tariff_version` groups the slab rows belonging to the same published
    tariff schedule (e.g. "TN-DOMESTIC-2026.1") so the tariff engine can
    select one coherent schedule rather than mixing slabs from different
    orders. All slabs of the same version must share the same
    effective_from/effective_to (not enforced by the database — the seed
    loader and Phase 5 tests are responsible for this invariant).

    Rows are only ever loaded from backend/app/data/tariffs/india/ by
    scripts/seed_tariffs.py, after being validated against an official
    source (see app.data_validation). Only VERIFIED, active rows are used
    for calculation. A state with no verified data stays unconfigured; the
    tariff engine reports that honestly rather than fabricating a rate.
    """

    __tablename__ = "electricity_tariffs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    union_territory: Mapped[str | None] = mapped_column(String(120), nullable=True)
    discom_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("discoms.id"), nullable=True)
    consumer_category: Mapped[TariffConsumerCategory] = mapped_column(
        Enum(TariffConsumerCategory), nullable=False
    )

    tariff_version: Mapped[str] = mapped_column(String(100), nullable=False)
    tariff_name: Mapped[str] = mapped_column(String(255), nullable=False)
    slab_min_kwh: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # None = this is the final, unlimited-upper-bound slab.
    slab_max_kwh: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    energy_charge_inr_per_kwh: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    fixed_charge_inr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # What fixed_charge_inr is per (see FixedChargeBasis). Stored as a plain
    # string so adding a basis never needs a Postgres enum migration.
    fixed_charge_basis: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Demand (kVA/sanctioned-load-based) charges exist in many real tariffs
    # but this app does not collect sanctioned load — see
    # app.engines.tariff.bill_calculation, which always reports this
    # component as "not_calculated" rather than guessing a kVA value.
    demand_charge_inr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    wheeling_charge_inr_per_kwh: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_order_number: Mapped[str | None] = mapped_column(String(160), nullable=True)
    source_order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_page: Mapped[str | None] = mapped_column(String(160), nullable=True)
    source_table: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Defaults to PENDING_REVIEW, never VERIFIED: a row is only trusted once
    # someone explicitly marks it verified against its source.
    verification_status: Mapped[IncentiveVerificationStatus] = mapped_column(
        Enum(IncentiveVerificationStatus),
        nullable=False,
        default=IncentiveVerificationStatus.PENDING_REVIEW,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
