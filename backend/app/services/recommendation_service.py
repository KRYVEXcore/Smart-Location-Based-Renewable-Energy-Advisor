import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.repositories.assessment_repository import AssessmentRepository
from app.engines.financial import FinancialInput, analyse, cost_context_for
from app.engines.financial.costs import load_cost_records
from app.engines.recommendation import RecommendationInput, recommend
from app.engines.recommendation.assumptions import DEFAULT_INCENTIVE_CAPACITY_KW, DEFAULT_INCENTIVE_TECHNOLOGY
from app.engines.tariff.consumer_category_mapping import map_building_type_to_consumer_category
from app.models.assessment import Assessment
from app.models.enums import RenewableTechnology
from app.schemas.financial import FinancialAnalysisResult
from app.schemas.incentive import IncentiveEvaluationResponse
from app.schemas.recommendation import RecommendationResult
from app.schemas.solar import SolarCalculationResponse
from app.schemas.tariff import TariffCalculationResponse
from app.schemas.wind import WindCalculationResponse
from app.services.incentive_evaluation_service import IncentiveEvaluationService
from app.services.location.location_service import LocationService
from app.services.solar_calculation_service import SolarCalculationService
from app.services.tariff_calculation_service import TariffCalculationService
from app.services.wind_calculation_service import WindCalculationService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EngineResults:
    """Everything the existing engines produced for one assessment. A section is None
    when its engine failed unexpectedly; the others are unaffected."""

    solar: SolarCalculationResponse | None
    wind: WindCalculationResponse | None
    tariff: TariffCalculationResponse | None
    incentives: IncentiveEvaluationResponse | None
    recommendation: RecommendationResult
    financial: FinancialAnalysisResult | None = None


class RecommendationService:
    """Assessment -> the EXISTING Solar, Wind, Tariff and Incentive services -> Recommendation
    Engine. It only orchestrates: no calculation happens here, and no AI is involved.
    """

    def __init__(self, db: Session, location_service: LocationService) -> None:
        self._db = db
        self._location_service = location_service
        self._assessments = AssessmentRepository(db)

    def recommend_for_assessment(self, assessment_id: uuid.UUID) -> RecommendationResult:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return self.evaluate(assessment, default_incentives=False).recommendation

    def financial_for_assessment(self, assessment_id: uuid.UUID) -> FinancialAnalysisResult:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        financial = self.evaluate(assessment, default_incentives=False).financial
        if financial is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Financial analysis is unavailable")
        return financial

    def evaluate(self, assessment: Assessment, *, default_incentives: bool = True) -> EngineResults:
        """Runs each engine through its own service. A failure in one leaves that section
        unavailable (None) instead of breaking the others."""
        db, loc, aid = self._db, self._location_service, assessment.id

        def run(name: str, call):
            try:
                return call()
            except Exception:
                logger.exception("Recommendation: %s calculation failed", name)
                return None

        solar = run("solar", lambda: SolarCalculationService(db, loc).calculate_for_assessment(aid))
        wind = run("wind", lambda: WindCalculationService(db, loc).calculate_for_assessment(aid))
        tariff = run("tariff", lambda: TariffCalculationService(db, loc).calculate_for_assessment(aid))

        incentive_results: list[IncentiveEvaluationResponse | None] = []

        def incentives_for(technology: str, capacity_kw: float) -> IncentiveEvaluationResponse | None:
            result = run(
                "incentives",
                lambda: IncentiveEvaluationService(db, loc).evaluate_for_assessment(
                    aid,
                    technology=RenewableTechnology(technology),
                    proposed_capacity_kw=Decimal(str(capacity_kw)),
                ),
            )
            incentive_results.append(result)
            return result

        constraints = assessment.constraints
        recommendation = recommend(
            RecommendationInput(
                monthly_consumption_kwh=_to_float(assessment.energy.monthly_consumption_kwh),
                roof_area_sqft=_to_float(constraints.roof_area_sqft),
                budget_inr=_to_float(constraints.budget_inr),
                backup_required=bool(constraints.backup_required),
                solar=solar,
                wind=wind,
                tariff=tariff,
            ),
            incentives_for,
        ).model_copy(update={"assessment_id": aid})

        if not incentive_results and default_incentives:
            incentives_for(DEFAULT_INCENTIVE_TECHNOLOGY, DEFAULT_INCENTIVE_CAPACITY_KW)
        incentives = incentive_results[-1] if incentive_results else None

        financial = run("financial", lambda: self._financial(assessment, recommendation, solar, tariff))
        if financial is not None:
            # The recommendation shows the analysis; its old cost note (also its first limitation) is replaced.
            old_note = recommendation.cost_context.note
            cost_context = cost_context_for(financial, _to_float(constraints.budget_inr))
            recommendation = recommendation.model_copy(
                update={
                    "cost_context": cost_context,
                    "limitations": [cost_context.note if item == old_note else item for item in recommendation.limitations],
                }
            )
        return EngineResults(solar, wind, tariff, incentives, recommendation, financial)

    def _financial(
        self,
        assessment: Assessment,
        recommendation: RecommendationResult,
        solar: SolarCalculationResponse | None,
        tariff: TariffCalculationResponse | None,
    ) -> FinancialAnalysisResult:
        """Gathers the inputs the Financial Analysis Engine needs from the existing results."""
        pick = next(
            (o for o in (solar.options if solar else []) if o.capacity_kw == recommendation.recommended_capacity_kw), None
        )
        location = solar.location if solar else None
        tariff_ok = tariff is not None and tariff.status == "ok" and tariff.tariff is not None
        return analyse(
            FinancialInput(
                recommendation=recommendation,
                state=(location.state or location.union_territory) if location else None,
                consumer_category=map_building_type_to_consumer_category(assessment.building.building_type).value,
                monthly_consumption_kwh=_to_float(assessment.energy.monthly_consumption_kwh),
                monthly_generation_kwh=pick.estimated_monthly_generation_kwh if pick else None,
                bill_at=TariffCalculationService(self._db, self._location_service).bill_model(assessment) if tariff_ok else None,
                tariff_name=tariff.tariff.tariff_name if tariff_ok else None,
                tariff_version=tariff.tariff.tariff_version if tariff_ok else None,
                cost_records=load_cost_records(),
            )
        )


def _to_float(value: object | None) -> float | None:
    return None if value is None else float(value)
