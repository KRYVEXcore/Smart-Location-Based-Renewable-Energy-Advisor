"""FastAPI wiring for ConsumptionEstimationService."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.consumption_estimation_service import ConsumptionEstimationService
from app.services.location.dependencies import get_location_service
from app.services.location.location_service import LocationService


def get_consumption_estimation_service(
    db: Annotated[Session, Depends(get_db)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
) -> ConsumptionEstimationService:
    return ConsumptionEstimationService(db, location_service)
