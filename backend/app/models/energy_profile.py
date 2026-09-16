import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, Uuid
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
    monthly_consumption_kwh: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # Reserved for a future phase; not derived or populated in Phase 2.
    annual_consumption_kwh: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="energy")
