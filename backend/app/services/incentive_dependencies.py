"""FastAPI wiring for IncentiveEvaluationService and
IncentiveProgramRepository — kept separate so the service itself stays
easy to unit-test with injected mocks.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories.incentive_program_repository import IncentiveProgramRepository
from app.services.incentive_evaluation_service import IncentiveEvaluationService
from app.services.location.dependencies import get_location_service
from app.services.location.location_service import LocationService


def get_incentive_evaluation_service(
    db: Annotated[Session, Depends(get_db)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
) -> IncentiveEvaluationService:
    return IncentiveEvaluationService(db, location_service)


def get_incentive_program_repository(db: Annotated[Session, Depends(get_db)]) -> IncentiveProgramRepository:
    return IncentiveProgramRepository(db)
