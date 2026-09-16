import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Discom(Base):
    """A registry of India's electricity distribution companies.

    Empty in production until populated from an authoritative source (e.g.
    each state electricity regulatory commission) — the app must never guess
    a DISCOM. Exactly one of state / union_territory is expected to be set.
    """

    __tablename__ = "discoms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    union_territory: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
