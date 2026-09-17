import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.repositories.assessment_repository import AssessmentRepository
from app.database.repositories.incentive_evaluation_snapshot_repository import (
    IncentiveEvaluationSnapshotRepository,
)
from app.database.repositories.incentive_program_repository import IncentiveProgramRepository
from app.engines.incentive.incentive_engine import evaluate_incentives
from app.engines.incentive.version import ENGINE_CALCULATION_VERSION
from app.engines.tariff.consumer_category_mapping import map_building_type_to_consumer_category
from app.models.assessment import Assessment
from app.models.enums import IncentiveLevel, RenewableTechnology, TariffConsumerCategory
from app.models.incentive_program import IncentiveProgram
from app.schemas.incentive import (
    IncentiveEligibilityResult,
    IncentiveEvaluationResponse,
    IncentiveEvaluationSummary,
    IncentiveLocationSummary,
    IncentiveProgramInput,
)
from app.schemas.location import IndiaLocationContext, LocationProfile
from app.services.location.location_service import LocationService

logger = logging.getLogger(__name__)


class IncentiveEvaluationService:
    """Orchestrates: Assessment -> Phase 3 LocationProfile (India context) ->
    consumer-category mapping (reused from Phase 5, never a second mapping)
    -> incentive programme lookup -> Incentive Engine -> response, and
    records a reproducibility snapshot. Contains no eligibility or
    calculation logic itself — see app.engines.incentive for that.

    Never re-derives location or DISCOM resolution — both come from the
    existing Phase 3 LocationService / India resolver, exactly as Phase 5's
    TariffCalculationService does.
    """

    def __init__(self, db: Session, location_service: LocationService) -> None:
        self.db = db
        self._location_service = location_service
        self._assessments = AssessmentRepository(db)
        self._programs = IncentiveProgramRepository(db)
        self._snapshots = IncentiveEvaluationSnapshotRepository(db)

    def evaluate_for_assessment(
        self,
        assessment_id: uuid.UUID,
        *,
        technology: RenewableTechnology,
        proposed_capacity_kw: Decimal,
        calculation_date: date | None = None,
    ) -> IncentiveEvaluationResponse:
        assessment = self._get_assessment(assessment_id)
        calc_date = calculation_date or date.today()

        if assessment.location.latitude is None or assessment.location.longitude is None:
            return self._insufficient(
                "This assessment has no saved coordinates, so its location cannot be resolved.",
                technology,
                proposed_capacity_kw,
            )

        profile = self._location_service.get_profile(
            float(assessment.location.latitude), float(assessment.location.longitude)
        )
        india = profile.india

        if india is None or (india.state is None and india.union_territory is None):
            return self._insufficient(
                "This location could not be resolved to an Indian state or union territory, "
                "so no incentive programme can be looked up.",
                technology,
                proposed_capacity_kw,
                profile=profile,
            )

        consumer_category = map_building_type_to_consumer_category(assessment.building.building_type)
        rows = self._programs.find_candidates(
            state=india.state,
            union_territory=india.union_territory,
            technology=technology,
        )
        scoped_rows, discom_blocked_results = self._scope_by_discom(rows, india)

        candidate_inputs = [_to_program_input(row) for row in scoped_rows]
        available_context = _build_context(assessment)

        engine_results = evaluate_incentives(
            candidate_inputs,
            calculation_date=calc_date,
            technology=technology,
            consumer_category=consumer_category,
            # This app collects no verified installation cost anywhere
            # (a user's own budget is not a vendor quotation) — see the
            # README's Phase 6 boundary notes. Never invented.
            eligible_cost_basis_inr=None,
            proposed_capacity_kw=proposed_capacity_kw,
            available_context=available_context,
        )
        all_results = engine_results + discom_blocked_results

        response = self._build_response(
            assessment_id, technology, proposed_capacity_kw, profile, india, consumer_category, all_results
        )
        self._record_snapshot(assessment_id, technology, proposed_capacity_kw, calc_date, consumer_category, response)

        return response

    def _get_assessment(self, assessment_id: uuid.UUID) -> Assessment:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return assessment

    def _scope_by_discom(
        self, rows: list[IncentiveProgram], india: IndiaLocationContext
    ) -> tuple[list[IncentiveProgram], list[IncentiveEligibilityResult]]:
        non_discom = [row for row in rows if row.discom_id is None]
        discom_rows = [row for row in rows if row.discom_id is not None]

        if not discom_rows:
            return non_discom, []

        if india.discom_status == "identified" and india.discom is not None:
            matching = [row for row in discom_rows if str(row.discom_id) == india.discom.id]
            return non_discom + matching, []

        # "ambiguous" or "not_identified": never guess which DISCOM's
        # programme applies — report each distinct blocked scheme
        # explicitly rather than silently omitting it.
        blocked_status = "discom_ambiguous" if india.discom_status == "ambiguous" else "discom_not_identified"
        reason = (
            "More than one electricity distribution company matches this location, so "
            "DISCOM-specific programmes cannot be determined without guessing."
            if blocked_status == "discom_ambiguous"
            else "This location could not be matched to a specific electricity distribution "
            "company, so DISCOM-specific programmes cannot be checked."
        )

        seen: set[tuple[str, IncentiveLevel, RenewableTechnology]] = set()
        placeholders: list[IncentiveEligibilityResult] = []
        for row in discom_rows:
            key = (row.scheme_name, row.level, row.technology)
            if key in seen:
                continue
            seen.add(key)
            placeholders.append(
                IncentiveEligibilityResult(
                    scheme_name=row.scheme_name,
                    level=row.level,
                    incentive_type=row.incentive_type,
                    technology=row.technology,
                    status=blocked_status,
                    eligible=False,
                    reason=reason,
                )
            )
        return non_discom, placeholders

    def _insufficient(
        self,
        reason: str,
        technology: RenewableTechnology,
        proposed_capacity_kw: Decimal,
        profile: LocationProfile | None = None,
    ) -> IncentiveEvaluationResponse:
        return IncentiveEvaluationResponse(
            status="insufficient_data",
            reason=reason,
            technology=technology,
            proposed_capacity_kw=str(proposed_capacity_kw),
            location=self._location_summary(profile, profile.india if profile else None) if profile else None,
            summary=IncentiveEvaluationSummary(calculation_status="insufficient_data"),
            calculation_version=ENGINE_CALCULATION_VERSION,
            calculated_at=datetime.now(UTC),
        )

    def _build_response(
        self,
        assessment_id: uuid.UUID,
        technology: RenewableTechnology,
        proposed_capacity_kw: Decimal,
        profile: LocationProfile,
        india: IndiaLocationContext,
        consumer_category: TariffConsumerCategory,
        results: list[IncentiveEligibilityResult],
    ) -> IncentiveEvaluationResponse:
        verified_programmes = sum(1 for r in results if r.status != "scheme_not_verified")
        eligible_programmes = sum(1 for r in results if r.eligible)
        calculation_status = "ok" if results else "no_programmes_found"

        return IncentiveEvaluationResponse(
            status="ok",
            assessment_id=assessment_id,
            technology=technology,
            proposed_capacity_kw=str(proposed_capacity_kw),
            location=self._location_summary(profile, india),
            consumer_category=consumer_category,
            programmes=results,
            summary=IncentiveEvaluationSummary(
                verified_programmes=verified_programmes,
                eligible_programmes=eligible_programmes,
                calculation_status=calculation_status,
            ),
            calculation_version=ENGINE_CALCULATION_VERSION,
            calculated_at=datetime.now(UTC),
        )

    def _location_summary(
        self, profile: LocationProfile | None, india: IndiaLocationContext | None
    ) -> IncentiveLocationSummary | None:
        if profile is None:
            return None
        return IncentiveLocationSummary(
            latitude=profile.latitude,
            longitude=profile.longitude,
            formatted_address=profile.formatted_address,
            city=profile.city,
            district=india.district if india else None,
            state=india.state if india else None,
            union_territory=india.union_territory if india else None,
            country=profile.country,
            discom_status=india.discom_status if india else "not_identified",
            discom_name=india.discom.name if india and india.discom else None,
        )

    def _record_snapshot(
        self,
        assessment_id: uuid.UUID,
        technology: RenewableTechnology,
        proposed_capacity_kw: Decimal,
        calc_date: date,
        consumer_category: TariffConsumerCategory,
        response: IncentiveEvaluationResponse,
    ) -> None:
        try:
            self._snapshots.record(
                assessment_id=assessment_id,
                calculation_version=response.calculation_version,
                input_snapshot={
                    "technology": technology.value,
                    "proposed_capacity_kw": str(proposed_capacity_kw),
                    "calculation_date": calc_date.isoformat(),
                    "consumer_category": consumer_category.value,
                },
                result_snapshot=response.model_dump(mode="json"),
            )
            self.db.commit()
        except Exception:
            logger.exception("Failed to record incentive evaluation snapshot (best-effort, non-fatal)")


def _to_decimal(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _to_decimal_or_none(value: object | None) -> Decimal | None:
    return None if value is None else _to_decimal(value)


def _build_context(assessment: Assessment) -> dict[str, object]:
    """Only fields this app actually collects. A scheme's eligibility_rules
    can name any field it wants — one not present here always resolves as
    missing (see app.engines.incentive.eligibility), never invented.
    """
    return {
        "monthly_consumption_kwh": _to_decimal_or_none(assessment.energy.monthly_consumption_kwh),
        "roof_area_sqft": _to_decimal_or_none(assessment.constraints.roof_area_sqft),
        "land_area_sqft": _to_decimal_or_none(assessment.constraints.land_area_sqft),
        "budget_inr": _to_decimal_or_none(assessment.constraints.budget_inr),
        "backup_required": assessment.constraints.backup_required,
    }


def _to_program_input(row: IncentiveProgram) -> IncentiveProgramInput:
    return IncentiveProgramInput(
        id=row.id,
        scheme_name=row.scheme_name,
        scheme_version=row.scheme_version,
        level=row.level,
        incentive_type=row.incentive_type,
        technology=row.technology,
        consumer_category=row.consumer_category,
        min_system_size_kw=_to_decimal_or_none(row.min_system_size_kw),
        max_system_size_kw=_to_decimal_or_none(row.max_system_size_kw),
        subsidy_type=row.subsidy_type,
        subsidy_value=_to_decimal_or_none(row.subsidy_value),
        percentage_value=_to_decimal_or_none(row.percentage_value),
        maximum_amount=_to_decimal_or_none(row.maximum_amount),
        calculation_rules=row.calculation_rules,
        eligibility_rules=row.eligibility_rules,
        stacking_rules=row.stacking_rules,
        effective_from=row.effective_from,
        effective_to=row.effective_to,
        verification_status=row.verification_status,
        active=row.active,
        source_name=row.source_name,
        source_url=row.source_url,
        source_document=row.source_document,
        last_verified=row.last_verified,
        discom_id=row.discom_id,
    )
