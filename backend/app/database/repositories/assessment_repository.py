import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.assessment import Assessment


def _with_relations(query: Select[tuple[Assessment]]) -> Select[tuple[Assessment]]:
    return query.options(
        joinedload(Assessment.building),
        joinedload(Assessment.location),
        joinedload(Assessment.energy),
        joinedload(Assessment.constraints),
    )


class AssessmentRepository:
    """Raw persistence access for assessments. No business rules here —
    see app.services.assessment_service.AssessmentService for that.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, assessment: Assessment) -> Assessment:
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def get(self, assessment_id: uuid.UUID) -> Assessment | None:
        query = _with_relations(select(Assessment).where(Assessment.id == assessment_id))
        return self.db.execute(query).unique().scalar_one_or_none()

    def list_recent(self, limit: int = 20) -> list[Assessment]:
        query = _with_relations(
            select(Assessment).order_by(Assessment.created_at.desc()).limit(limit)
        )
        return list(self.db.execute(query).unique().scalars())

    def delete(self, assessment: Assessment) -> None:
        self.db.delete(assessment)
        self.db.flush()
