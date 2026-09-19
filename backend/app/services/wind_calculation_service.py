import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.repositories.assessment_repository import AssessmentRepository
from app.database.repositories.wind_calculation_snapshot_repository import (
    WindCalculationSnapshotRepository,
)
from app.engines.wind import calculate as run_wind_engine
from app.engines.wind.assumptions import ASSUMPTION_VERSION, ENGINE_CALCULATION_VERSION, LIMITATIONS
from app.models.assessment import Assessment
from app.schemas.location import LocationProfile
from app.schemas.wind import WindCalculationResponse, WindEngineInput, WindLocationSummary
from app.services.location.location_service import LocationService

logger = logging.getLogger(__name__)


class WindCalculationService:
    """Assessment -> Phase 3 LocationProfile (India context + wind resource)
    -> Wind Engine -> response, plus a reproducibility snapshot. No
    calculation logic lives here (see app.engines.wind), and the wind
    resource always comes from Phase 3 - never fetched or defaulted here.
    """

    def __init__(self, db: Session, location_service: LocationService) -> None:
        self.db = db
        self._location_service = location_service
        self._assessments = AssessmentRepository(db)
        self._snapshots = WindCalculationSnapshotRepository(db)

    def calculate_for_assessment(self, assessment_id: uuid.UUID) -> WindCalculationResponse:
        assessment = self._get_assessment(assessment_id)

        if assessment.location.latitude is None or assessment.location.longitude is None:
            return self._location_unavailable(
                assessment_id, "This assessment has no saved coordinates, so its wind resource cannot be looked up."
            )

        profile = self._location_service.get_profile(
            float(assessment.location.latitude), float(assessment.location.longitude)
        )
        india = profile.india
        if india is None or (india.state is None and india.union_territory is None):
            return self._location_unavailable(
                assessment_id,
                "This location could not be resolved to an Indian state or union territory, "
                "so no India-based wind screening is calculated.",
                profile,
            )

        engine_input = WindEngineInput(
            wind_resource=profile.wind,
            roof_area_sqft=_to_float(assessment.constraints.roof_area_sqft),
            land_area_sqft=_to_float(assessment.constraints.land_area_sqft),
        )
        result = run_wind_engine(engine_input).model_copy(
            update={"assessment_id": assessment_id, "location": _summary(profile)}
        )
        self._record_snapshot(assessment_id, engine_input, result)
        return result

    def _get_assessment(self, assessment_id: uuid.UUID) -> Assessment:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return assessment

    def _location_unavailable(
        self, assessment_id: uuid.UUID, reason: str, profile: LocationProfile | None = None
    ) -> WindCalculationResponse:
        return WindCalculationResponse(
            status="location_unavailable",
            reason=reason,
            assessment_id=assessment_id,
            location=_summary(profile) if profile else None,
            limitations=LIMITATIONS,
            calculation_version=ENGINE_CALCULATION_VERSION,
            assumption_version=ASSUMPTION_VERSION,
            calculated_at=datetime.now(UTC),
        )

    def _record_snapshot(
        self, assessment_id: uuid.UUID, engine_input: WindEngineInput, result: WindCalculationResponse
    ) -> None:
        try:
            self._snapshots.record(
                assessment_id=assessment_id,
                calculation_version=result.calculation_version,
                assumption_version=result.assumption_version,
                input_snapshot=engine_input.model_dump(mode="json"),
                result_snapshot=result.model_dump(mode="json"),
            )
            self.db.commit()
        except Exception:
            logger.exception("Failed to record wind calculation snapshot (best-effort, non-fatal)")


def _to_float(value: object | None) -> float | None:
    return None if value is None else float(value)


def _summary(profile: LocationProfile) -> WindLocationSummary:
    india = profile.india
    return WindLocationSummary(
        latitude=profile.latitude,
        longitude=profile.longitude,
        formatted_address=profile.formatted_address,
        city=profile.city,
        district=india.district if india else None,
        state=india.state if india else None,
        union_territory=india.union_territory if india else None,
        country=profile.country,
    )
