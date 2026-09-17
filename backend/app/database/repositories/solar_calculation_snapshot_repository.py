import uuid

from sqlalchemy.orm import Session

from app.models.solar_calculation_snapshot import SolarCalculationSnapshot


class SolarCalculationSnapshotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        assessment_id: uuid.UUID,
        calculation_version: str,
        assumption_version: str,
        input_snapshot: dict,
        result_snapshot: dict,
    ) -> SolarCalculationSnapshot:
        snapshot = SolarCalculationSnapshot(
            assessment_id=assessment_id,
            calculation_version=calculation_version,
            assumption_version=assumption_version,
            input_snapshot=input_snapshot,
            result_snapshot=result_snapshot,
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot
