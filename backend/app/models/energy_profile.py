import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment


class EnergyProfile(Base):
    __tablename__ = "energy_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id"), nullable=False, unique=True
    )
    # The kWh figure every engine uses. It is the user's own number, or (bill-first
    # assessments) an ESTIMATE derived from the bill; consumption_source says which.
    # NULL means the estimate could not be made - it is never filled with a default.
    monthly_consumption_kwh: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # What the customer entered first: their average monthly electricity bill (INR).
    monthly_electricity_bill_inr: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    # 'user_kwh' (the user gave the units) or 'user_bill_estimate' (derived from the bill).
    consumption_source: Mapped[str] = mapped_column(String(30), nullable=False, default="user_kwh", server_default="user_kwh")
    # How a bill estimate was made (method, tariff used, range, limitations).
    consumption_estimate: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Reserved for a future phase; not derived or populated in Phase 2.
    annual_consumption_kwh: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="energy")
