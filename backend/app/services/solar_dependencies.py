"""FastAPI wiring for SolarCalculationService — kept separate so the
service itself stays easy to unit-test with injected mocks.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.location.dependencies import get_location_service
from app.services.location.location_service import LocationService
from app.services.solar_calculation_service import SolarCalculationService


def get_solar_calculation_service(
    db: Annotated[Session, Depends(get_db)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
) -> SolarCalculationService:
    return SolarCalculationService(db, location_service)
