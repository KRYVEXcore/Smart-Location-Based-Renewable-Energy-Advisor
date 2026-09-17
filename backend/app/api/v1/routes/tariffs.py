import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.database.repositories.tariff_repository import TariffRepository
from app.models.enums import TariffConsumerCategory
from app.schemas.tariff import TariffCalculateRequest, TariffCalculationResponse, TariffSlabOut
from app.services.tariff_calculation_service import TariffCalculationService
from app.services.tariff_dependencies import get_tariff_calculation_service, get_tariff_repository

router = APIRouter()

ServiceDep = Annotated[TariffCalculationService, Depends(get_tariff_calculation_service)]
RepoDep = Annotated[TariffRepository, Depends(get_tariff_repository)]


@router.post(
    "/tariffs/calculate",
    response_model=TariffCalculationResponse,
    summary="Calculate an estimated baseline electricity bill for an assessment",
)
def calculate_tariff(payload: TariffCalculateRequest, service: ServiceDep) -> TariffCalculationResponse:
    return service.calculate_for_assessment(payload.assessment_id, payload.calculation_date)


@router.get(
    "/tariffs",
    response_model=list[TariffSlabOut],
    summary="Look up configured tariff slabs by state/DISCOM/category",
)
def list_tariffs(
    repo: RepoDep,
    state: str | None = None,
    union_territory: str | None = None,
    consumer_category: TariffConsumerCategory | None = None,
    discom_id: uuid.UUID | None = None,
) -> list[TariffSlabOut]:
    rows = repo.find_filtered(
        state=state,
        union_territory=union_territory,
        consumer_category=consumer_category,
        discom_id=discom_id,
    )
    return [TariffSlabOut.model_validate(row) for row in rows]
