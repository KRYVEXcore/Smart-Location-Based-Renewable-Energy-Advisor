import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.database.repositories.incentive_program_repository import IncentiveProgramRepository
from app.models.enums import IncentiveLevel, RenewableTechnology, TariffConsumerCategory
from app.schemas.incentive import IncentiveEvaluateRequest, IncentiveEvaluationResponse, IncentiveProgramOut
from app.services.incentive_dependencies import get_incentive_evaluation_service, get_incentive_program_repository
from app.services.incentive_evaluation_service import IncentiveEvaluationService

router = APIRouter()

ServiceDep = Annotated[IncentiveEvaluationService, Depends(get_incentive_evaluation_service)]
RepoDep = Annotated[IncentiveProgramRepository, Depends(get_incentive_program_repository)]


@router.post(
    "/incentives/evaluate",
    response_model=IncentiveEvaluationResponse,
    summary="Evaluate applicable renewable-energy incentive programmes for an assessment",
)
def evaluate_incentives(payload: IncentiveEvaluateRequest, service: ServiceDep) -> IncentiveEvaluationResponse:
    # The frontend only ever submits assessment/context (assessment_id,
    # technology, proposed capacity) — never a subsidy rate or amount. The
    # backend always selects verified programme data itself; see the
    # README's Phase 6 security note.
    return service.evaluate_for_assessment(
        payload.assessment_id,
        technology=payload.technology,
        proposed_capacity_kw=payload.proposed_capacity_kw,
        calculation_date=payload.calculation_date,
    )


@router.get(
    "/incentives",
    response_model=list[IncentiveProgramOut],
    summary="Look up configured incentive programmes by state/DISCOM/technology/category",
)
def list_incentives(
    repo: RepoDep,
    state: str | None = None,
    union_territory: str | None = None,
    discom_id: uuid.UUID | None = None,
    technology: RenewableTechnology | None = None,
    consumer_category: TariffConsumerCategory | None = None,
    level: IncentiveLevel | None = None,
) -> list[IncentiveProgramOut]:
    rows = repo.find_filtered(
        state=state,
        union_territory=union_territory,
        discom_id=discom_id,
        technology=technology,
        consumer_category=consumer_category,
        level=level,
    )
    return [IncentiveProgramOut.model_validate(row) for row in rows]
