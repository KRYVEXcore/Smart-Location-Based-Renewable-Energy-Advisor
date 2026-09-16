import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.models.enums import BuildingType


class ElectricityTariff(Base):
    """A single tariff slab, scoped to a state/UT, optionally a DISCOM, and a
    consumer category. Real tariff orders are published as several slabs
    (e.g. 0-100 kWh, 101-300 kWh, ...) — one row per slab.

    No production rows are seeded by this migration. Populating this table
    from real DISCOM tariff orders, and the engine that resolves a user's
    exact tariff, are future work (see the README's Location Intelligence /
    tariff architecture notes) — this only prepares the schema.
    """

    __tablename__ = "electricity_tariffs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    union_territory: Mapped[str | None] = mapped_column(String(120), nullable=True)
    discom_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("discoms.id"), nullable=True)
    consumer_category: Mapped[BuildingType] = mapped_column(Enum(BuildingType), nullable=False)

    tariff_name: Mapped[str] = mapped_column(String(255), nullable=False)
    slab_min_kwh: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    slab_max_kwh: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    energy_charge_inr_per_kwh: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    fixed_charge_inr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    demand_charge_inr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

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
