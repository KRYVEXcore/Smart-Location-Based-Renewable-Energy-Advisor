"""FastAPI wiring for AdvisorService."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.connection import get_db
from app.services.advisor_service import AdvisorService
from app.services.ai.provider import ChatProvider, build_provider
from app.services.ai.rate_limit import SlidingWindowLimiter, chat_rate_limiter
from app.services.location.dependencies import get_location_service
from app.services.location.location_service import LocationService
from app.services.prototype_user import PROTOTYPE_USER_ID


def get_chat_provider(settings: Annotated[Settings, Depends(get_settings)]) -> ChatProvider | None:
    return build_provider(settings)


def get_chat_rate_limiter() -> SlidingWindowLimiter:
    return chat_rate_limiter


def get_current_user_id() -> uuid.UUID:
    # There is no authentication yet (see app.services.prototype_user), so every
    # caller is the prototype user and an assessment is reachable only by its
    # unguessable id, exactly like GET /assessments/{id}. The advisor already
    # checks ownership against this value, so real auth only replaces this function.
    return PROTOTYPE_USER_ID


def get_advisor_service(
    db: Annotated[Session, Depends(get_db)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
    provider: Annotated[ChatProvider | None, Depends(get_chat_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[SlidingWindowLimiter, Depends(get_chat_rate_limiter)],
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> AdvisorService:
    return AdvisorService(db, location_service, provider, settings, limiter, current_user_id)
