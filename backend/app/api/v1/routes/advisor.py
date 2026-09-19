import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.advisor import AdvisorChatRequest, AdvisorChatResponse, AdvisorOverviewResponse
from app.services.advisor_dependencies import get_advisor_service
from app.services.advisor_service import AdvisorService

router = APIRouter()

ServiceDep = Annotated[AdvisorService, Depends(get_advisor_service)]


@router.post(
    "/advisor/chat",
    response_model=AdvisorChatResponse,
    summary="Ask SHREA AI about an assessment (one AI call per message; explains verified results only)",
)
def chat(payload: AdvisorChatRequest, service: ServiceDep) -> AdvisorChatResponse:
    return service.chat(payload)


@router.get(
    "/advisor/overview/{assessment_id}",
    response_model=AdvisorOverviewResponse,
    summary="Assessment summary and suggested questions for the chat panel (makes no AI call)",
)
def overview(assessment_id: uuid.UUID, service: ServiceDep) -> AdvisorOverviewResponse:
    return service.overview(assessment_id)
