import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.financial import FinancialAnalysisResult
from app.services.recommendation_dependencies import get_recommendation_service
from app.services.recommendation_service import RecommendationService

router = APIRouter()

ServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


@router.get(
    "/financial-analysis/{assessment_id}",
    response_model=FinancialAnalysisResult,
    summary="Deterministic estimated cost, incentive, savings and simple payback for the recommended system (no AI)",
)
def get_financial_analysis(assessment_id: uuid.UUID, service: ServiceDep) -> FinancialAnalysisResult:
    return service.financial_for_assessment(assessment_id)
