import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment


class BuildingConstraints(Base):
    __tablename__ = "building_constraints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id"), nullable=False, unique=True
    )
    roof_area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    land_area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_inr: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    backup_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    assessment: Mapped["Assessment"] = relationship(back_populates="constraints")
