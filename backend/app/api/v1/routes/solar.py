from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.solar import SolarCalculateRequest, SolarCalculationResponse
from app.services.solar_calculation_service import SolarCalculationService
from app.services.solar_dependencies import get_solar_calculation_service

router = APIRouter()

ServiceDep = Annotated[SolarCalculationService, Depends(get_solar_calculation_service)]


@router.post(
    "/solar/calculate",
    response_model=SolarCalculationResponse,
    summary="Calculate technical solar system options for an assessment",
)
def calculate_solar(payload: SolarCalculateRequest, service: ServiceDep) -> SolarCalculationResponse:
    return service.calculate_for_assessment(payload.assessment_id)
