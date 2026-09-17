import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class IncentiveEvaluationSnapshot(Base):
    """Audit trail supporting reproducibility: what was evaluated, with
    which engine version, and the exact input and result. Not read back by
    the engine itself — a write-through log, same pattern as
    SolarCalculationSnapshot (Phase 4) and TariffCalculationSnapshot
    (Phase 5).
    """

    __tablename__ = "incentive_evaluation_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # ondelete="CASCADE" from day one — see the Phase 4 fix note for the
    # same issue on solar_calculation_snapshots (a missing CASCADE there
    # once broke DELETE /assessments/{id}).
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    calculation_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
