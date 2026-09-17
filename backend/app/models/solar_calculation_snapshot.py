import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SolarCalculationSnapshot(Base):
    """Audit trail supporting reproducibility: what was calculated, with
    which engine/assumption versions, and the exact input and result. Not
    read back by the engine itself — a write-through log, same pattern as
    LocationResourceSnapshot (Phase 3).
    """

    __tablename__ = "solar_calculation_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # ondelete="CASCADE": this is a write-only audit log, not a record an
    # assessment owner needs preserved independently — deleting the
    # assessment (Phase 2's DELETE /assessments/{id}) must not be blocked
    # by its own calculation history.
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    calculation_version: Mapped[str] = mapped_column(String(50), nullable=False)
    assumption_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
