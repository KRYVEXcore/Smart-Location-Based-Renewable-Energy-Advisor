import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.enums import AssessmentStatus

if TYPE_CHECKING:
    from app.models.building import Building
    from app.models.building_constraints import BuildingConstraints
    from app.models.energy_profile import EnergyProfile
    from app.models.location import Location


class Assessment(Base):
    """A single saved assessment. Phase 2 stores inputs only — no renewable
    generation, cost, or recommendation results are calculated or stored yet.
    """

    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("buildings.id"), nullable=False)
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus), nullable=False, default=AssessmentStatus.SUBMITTED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    building: Mapped["Building"] = relationship(back_populates="assessments")
    location: Mapped["Location"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    energy: Mapped["EnergyProfile"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    constraints: Mapped["BuildingConstraints"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
