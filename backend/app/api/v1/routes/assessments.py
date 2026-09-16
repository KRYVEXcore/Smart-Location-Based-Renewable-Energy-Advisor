import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.assessment import AssessmentCreate, AssessmentResponse, AssessmentUpdate
from app.services.assessment_service import AssessmentService

router = APIRouter()


def get_assessment_service(db: Annotated[Session, Depends(get_db)]) -> AssessmentService:
    return AssessmentService(db)


ServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]


@router.post(
    "/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and persist a new assessment",
)
def create_assessment(payload: AssessmentCreate, service: ServiceDep) -> AssessmentResponse:
    assessment = service.create_assessment(payload)
    return AssessmentResponse.model_validate(assessment)


@router.get(
    "/assessments",
    response_model=list[AssessmentResponse],
    summary="List recent assessments",
)
def list_assessments(service: ServiceDep, limit: int = 20) -> list[AssessmentResponse]:
    assessments = service.list_assessments(limit=limit)
    return [AssessmentResponse.model_validate(assessment) for assessment in assessments]


@router.get(
    "/assessments/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Retrieve a saved assessment",
)
def get_assessment(assessment_id: uuid.UUID, service: ServiceDep) -> AssessmentResponse:
    assessment = service.get_assessment(assessment_id)
    return AssessmentResponse.model_validate(assessment)


@router.put(
    "/assessments/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Update an existing assessment",
)
def update_assessment(
    assessment_id: uuid.UUID, payload: AssessmentUpdate, service: ServiceDep
) -> AssessmentResponse:
    assessment = service.update_assessment(assessment_id, payload)
    return AssessmentResponse.model_validate(assessment)


@router.delete(
    "/assessments/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assessment",
)
def delete_assessment(assessment_id: uuid.UUID, service: ServiceDep) -> Response:
    service.delete_assessment(assessment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
