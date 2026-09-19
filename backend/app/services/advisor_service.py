import json
import logging
import time
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.repositories.assessment_repository import AssessmentRepository
from app.models.assessment import Assessment
from app.models.enums import RenewableTechnology
from app.schemas.advisor import AdvisorChatRequest, AdvisorChatResponse, AdvisorOverviewResponse
from app.services.ai.context import (
    INCENTIVE_CAPACITY_KW,
    INCENTIVE_TECHNOLOGY,
    available_topics,
    build_advisor_context,
    suggested_questions,
)
from app.services.ai.prompt import SYSTEM_PROMPT
from app.services.ai.provider import AIProviderError, ChatProvider
from app.services.ai.rate_limit import SlidingWindowLimiter
from app.services.incentive_evaluation_service import IncentiveEvaluationService
from app.services.location.location_service import LocationService
from app.services.solar_calculation_service import SolarCalculationService
from app.services.tariff_calculation_service import TariffCalculationService
from app.services.wind_calculation_service import WindCalculationService

logger = logging.getLogger(__name__)

MAX_REPLY_CHARS = 4000


class AdvisorService:
    """SHREA AI: assessment -> existing engine services -> compact context ->
    provider. The model only explains results; every number it can see was
    produced by the deterministic engines. No tool, database, filesystem or
    network access is given to it.
    """

    def __init__(
        self,
        db: Session,
        location_service: LocationService,
        provider: ChatProvider | None,
        settings: Settings,
        limiter: SlidingWindowLimiter,
        current_user_id: uuid.UUID,
    ) -> None:
        self._db = db
        self._location_service = location_service
        self._provider = provider
        self._settings = settings
        self._limiter = limiter
        self._current_user_id = current_user_id
        self._assessments = AssessmentRepository(db)

    def overview(self, assessment_id: uuid.UUID) -> AdvisorOverviewResponse:
        assessment = self._get_assessment(assessment_id)
        context = self._build_context(assessment)
        topics = available_topics(context)
        location = context.get("location", {})
        label = ", ".join(p for p in (location.get("city"), location.get("state")) if p) or None
        return AdvisorOverviewResponse(
            assessment_id=assessment_id,
            ai_configured=self._provider is not None,
            location_label=label,
            building_type=context["assessment"]["building_type"],
            monthly_consumption_kwh=context["assessment"].get("monthly_consumption_kwh"),
            available=topics,
            suggested_questions=suggested_questions(topics),
        )

    def chat(self, request: AdvisorChatRequest) -> AdvisorChatResponse:
        assessment = self._get_assessment(request.assessment_id)
        if self._provider is None:
            return AdvisorChatResponse(
                status="ai_not_configured", error_code="ai_not_configured", assessment_id=request.assessment_id
            )
        self._enforce_rate_limit(request.assessment_id)

        started = time.monotonic()
        provider = self._provider
        try:
            context = self._build_context(assessment)
            system = (
                SYSTEM_PROMPT
                + "\nAPPLICATION DATA (authoritative, JSON):\n"
                + json.dumps(context, separators=(",", ":"), ensure_ascii=False)
            )
            history = request.history[-self._settings.ai_history_limit :]
            messages = [{"role": t.role, "content": t.content} for t in history]
            messages.append({"role": "user", "content": request.message})
            reply = self._validate_reply(provider.complete(system, messages))
        except AIProviderError as error:
            self._log(provider, request.assessment_id, error.code, started)
            return AdvisorChatResponse(
                status="ai_error",
                error_code=error.code,
                assessment_id=request.assessment_id,
                provider=provider.name,
                model=provider.model,
            )
        self._log(provider, request.assessment_id, "ok", started)
        return AdvisorChatResponse(
            status="ok",
            message=reply,
            assessment_id=request.assessment_id,
            provider=provider.name,
            model=provider.model,
        )

    def _get_assessment(self, assessment_id: uuid.UUID) -> Assessment:
        assessment = self._assessments.get(assessment_id)
        # A missing assessment and one owned by someone else look identical.
        if assessment is None or assessment.building.user_id != self._current_user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return assessment

    def _enforce_rate_limit(self, assessment_id: uuid.UUID) -> None:
        settings = self._settings
        if not self._limiter.allow(f"assessment:{assessment_id}", settings.ai_rate_limit_per_minute) or not (
            self._limiter.allow("global", settings.ai_global_rate_limit_per_minute)
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many advisor requests. Please wait a minute and try again.",
            )

    def _build_context(self, assessment: Assessment) -> dict:
        """Each engine runs through its own existing service; a failure in one
        leaves that section 'unavailable' rather than breaking the others."""
        db, loc, aid = self._db, self._location_service, assessment.id

        def run(name: str, call):
            try:
                return call()
            except Exception:
                logger.exception("Advisor context: %s calculation failed", name)
                return None

        return build_advisor_context(
            assessment,
            solar=run("solar", lambda: SolarCalculationService(db, loc).calculate_for_assessment(aid)),
            wind=run("wind", lambda: WindCalculationService(db, loc).calculate_for_assessment(aid)),
            tariff=run("tariff", lambda: TariffCalculationService(db, loc).calculate_for_assessment(aid)),
            incentives=run(
                "incentives",
                lambda: IncentiveEvaluationService(db, loc).evaluate_for_assessment(
                    aid,
                    technology=RenewableTechnology(INCENTIVE_TECHNOLOGY),
                    proposed_capacity_kw=Decimal(INCENTIVE_CAPACITY_KW),
                ),
            ),
        )

    def _validate_reply(self, text: str) -> str:
        text = text.strip()
        if not text:
            raise AIProviderError("invalid_response")
        key = self._settings.nvidia_api_key
        if key and key in text:
            raise AIProviderError("invalid_response")
        return text if len(text) <= MAX_REPLY_CHARS else text[:MAX_REPLY_CHARS].rstrip() + "…"

    @staticmethod
    def _log(provider: ChatProvider, assessment_id: uuid.UUID, outcome: str, started: float) -> None:
        logger.info(
            "advisor_chat provider=%s model=%s assessment=%s outcome=%s latency_ms=%d",
            provider.name,
            provider.model,
            assessment_id,
            outcome,
            (time.monotonic() - started) * 1000,
        )
