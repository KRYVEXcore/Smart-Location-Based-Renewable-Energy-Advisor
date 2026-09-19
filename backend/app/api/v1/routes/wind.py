from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.wind import WindCalculateRequest, WindCalculationResponse
from app.services.wind_calculation_service import WindCalculationService
from app.services.wind_dependencies import get_wind_calculation_service

router = APIRouter()

ServiceDep = Annotated[WindCalculationService, Depends(get_wind_calculation_service)]


@router.post(
    "/wind/calculate",
    response_model=WindCalculationResponse,
    summary="Screen small-wind candidate systems for an assessment (technical only, not a recommendation)",
)
def calculate_wind(payload: WindCalculateRequest, service: ServiceDep) -> WindCalculationResponse:
    return service.calculate_for_assessment(payload.assessment_id)
