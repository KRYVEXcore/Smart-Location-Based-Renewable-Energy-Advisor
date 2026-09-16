import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.enums import BuildingType

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.user import User


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    building_type: Mapped[BuildingType] = mapped_column(Enum(BuildingType), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="buildings")
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="building", cascade="all, delete-orphan"
    )
