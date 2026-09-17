"""FastAPI wiring for TariffCalculationService and TariffRepository — kept
separate so the service itself stays easy to unit-test with injected mocks.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.repositories.tariff_repository import TariffRepository
from app.services.location.dependencies import get_location_service
from app.services.location.location_service import LocationService
from app.services.tariff_calculation_service import TariffCalculationService


def get_tariff_calculation_service(
    db: Annotated[Session, Depends(get_db)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
) -> TariffCalculationService:
    return TariffCalculationService(db, location_service)


def get_tariff_repository(db: Annotated[Session, Depends(get_db)]) -> TariffRepository:
    return TariffRepository(db)
