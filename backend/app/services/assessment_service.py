import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.repositories.assessment_repository import AssessmentRepository
from app.models.assessment import Assessment
from app.models.building import Building
from app.models.building_constraints import BuildingConstraints
from app.models.energy_profile import EnergyProfile
from app.models.enums import AssessmentStatus
from app.models.location import Location
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate
from app.services.prototype_user import get_or_create_prototype_user


class AssessmentService:
    """Orchestrates assessment persistence.

    Contains no renewable-energy calculations — Phase 2 only collects and
    stores assessment inputs. Sizing, cost, and recommendation logic belongs
    to the engines in app.engines, added in later phases.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AssessmentRepository(db)

    def create_assessment(self, payload: AssessmentCreate) -> Assessment:
        user = get_or_create_prototype_user(self.db)

        building = Building(
            user_id=user.id,
            building_type=payload.building.building_type,
            name=payload.building.name,
        )
        assessment = Assessment(building=building, status=AssessmentStatus.SUBMITTED)
        assessment.location = Location(**payload.location.model_dump())
        assessment.energy = EnergyProfile(
            monthly_consumption_kwh=payload.energy.monthly_consumption_kwh
        )
        assessment.constraints = BuildingConstraints(**payload.constraints.model_dump())

        self.repository.add(assessment)
        self.db.commit()
        return self._reload(assessment.id)

    def get_assessment(self, assessment_id: uuid.UUID) -> Assessment:
        assessment = self.repository.get(assessment_id)
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        return assessment

    def list_assessments(self, limit: int = 20) -> list[Assessment]:
        return self.repository.list_recent(limit=limit)

    def update_assessment(self, assessment_id: uuid.UUID, payload: AssessmentUpdate) -> Assessment:
        assessment = self.get_assessment(assessment_id)

        if payload.building is not None:
            assessment.building.building_type = payload.building.building_type
            assessment.building.name = payload.building.name
        if payload.location is not None:
            for field, value in payload.location.model_dump().items():
                setattr(assessment.location, field, value)
        if payload.energy is not None:
            assessment.energy.monthly_consumption_kwh = payload.energy.monthly_consumption_kwh
        if payload.constraints is not None:
            for field, value in payload.constraints.model_dump().items():
                setattr(assessment.constraints, field, value)
        if payload.status is not None:
            assessment.status = payload.status

        # Modifying only a related child (location/energy/constraints) does
        # not touch the assessments row itself, so onupdate=func.now() would
        # never fire without an explicit touch here.
        assessment.updated_at = datetime.now(UTC)

        self.db.commit()
        return self._reload(assessment.id)

    def delete_assessment(self, assessment_id: uuid.UUID) -> None:
        assessment = self.get_assessment(assessment_id)
        self.repository.delete(assessment)
        self.db.commit()

    def _reload(self, assessment_id: uuid.UUID) -> Assessment:
        """Re-fetch with eager-loaded relations after a commit so the
        response is built from fresh, fully-loaded data.
        """
        assessment = self.repository.get(assessment_id)
        assert assessment is not None
        return assessment
