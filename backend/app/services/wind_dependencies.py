"""FastAPI wiring for WindCalculationService."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.location.dependencies import get_location_service
from app.services.location.location_service import LocationService
from app.services.wind_calculation_service import WindCalculationService


def get_wind_calculation_service(
    db: Annotated[Session, Depends(get_db)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
) -> WindCalculationService:
    return WindCalculationService(db, location_service)
