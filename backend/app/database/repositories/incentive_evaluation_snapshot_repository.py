import uuid

from sqlalchemy.orm import Session

from app.models.incentive_evaluation_snapshot import IncentiveEvaluationSnapshot


class IncentiveEvaluationSnapshotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        assessment_id: uuid.UUID,
        calculation_version: str,
        input_snapshot: dict,
        result_snapshot: dict,
    ) -> IncentiveEvaluationSnapshot:
        snapshot = IncentiveEvaluationSnapshot(
            assessment_id=assessment_id,
            calculation_version=calculation_version,
            input_snapshot=input_snapshot,
            result_snapshot=result_snapshot,
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot
