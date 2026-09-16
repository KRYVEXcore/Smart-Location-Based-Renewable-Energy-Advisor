from datetime import datetime

from sqlalchemy.orm import Session

from app.models.location_resource_snapshot import LocationResourceSnapshot


class LocationResourceSnapshotRepository:
    """Write-through audit log of provider fetches. See the model docstring."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        latitude: float,
        longitude: float,
        resource_type: str,
        provider: str,
        payload: dict,
        retrieved_at: datetime,
    ) -> LocationResourceSnapshot:
        snapshot = LocationResourceSnapshot(
            latitude=latitude,
            longitude=longitude,
            resource_type=resource_type,
            provider=provider,
            payload=payload,
            retrieved_at=retrieved_at,
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot
