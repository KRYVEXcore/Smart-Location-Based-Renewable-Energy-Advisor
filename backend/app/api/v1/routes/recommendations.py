import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.recommendation import RecommendationResult
from app.services.recommendation_dependencies import get_recommendation_service
from app.services.recommendation_service import RecommendationService

router = APIRouter()

ServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


@router.get(
    "/recommendations/{assessment_id}",
    response_model=RecommendationResult,
    summary="Deterministic technology and size recommendation built from the existing engines (no AI)",
)
def get_recommendation(assessment_id: uuid.UUID, service: ServiceDep) -> RecommendationResult:
    return service.recommend_for_assessment(assessment_id)
