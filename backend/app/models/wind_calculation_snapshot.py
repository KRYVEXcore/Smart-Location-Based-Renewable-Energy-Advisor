import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class WindCalculationSnapshot(Base):
    """Write-through audit log (same pattern as SolarCalculationSnapshot):
    the exact resource input, result, and engine/assumption versions, so a
    calculation can be reproduced. Not read back by the engine.
    """

    __tablename__ = "wind_calculation_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # CASCADE: deleting an assessment must not be blocked by its own log.
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    calculation_version: Mapped[str] = mapped_column(String(50), nullable=False)
    assumption_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
