import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class LocationResourceSnapshot(Base):
    """An audit trail of what was retrieved from a resource provider, when.

    Keyed by coordinate rather than a specific assessment's Location row,
    since GET /locations/profile takes a raw latitude/longitude — the same
    snapshot is reusable for any assessment at that coordinate. This is a
    write-through log, not the primary cache (see app.services.location.cache
    for the in-memory cache LocationService checks first).
    """

    __tablename__ = "location_resource_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
