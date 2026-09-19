import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.repositories.assessment_repository import AssessmentRepository
from app.database.repositories.solar_calculation_snapshot_repository import (
    SolarCalculationSnapshotRepository,
)
from app.engines.solar import calculate as run_solar_engine
from app.engines.solar.assumptions import ASSUMPTION_VERSION, ENGINE_CALCULATION_VERSION
from app.models.assessment import Assessment
from app.schemas.location import LocationProfile
from app.schemas.solar import (
    SolarCalculationResponse,
    SolarDataSource,
    SolarEngineInput,
    SolarLocationSummary,
)
from app.services.location.location_service import LocationService

logger = logging.getLogger(__name__)


class SolarCalculationService:
    """Orchestrates: Assessment -> Phase 3 LocationProfile -> Solar Engine ->
    response, and records a reproducibility snapshot. Contains no
    calculation logic itself — see app.engines.solar for that.
    """

    def __init__(self, db: Session, location_service: LocationService) -> None:
        self.db = db
        self._location_service = location_service
        self._assessments = AssessmentRepository(db)
        self._snapshots = SolarCalculationSnapshotRepository(db)

    def calculate_for_assessment(self, assessment_id: uuid.UUID) -> SolarCalculationResponse:
        assessment = self._get_assessment(assessment_id)

        if assessment.location.latitude is None or assessment.location.longitude is None:
            return self._insufficient(
                "This assessment has no saved coordinates, so location intelligence "
                "cannot be retrieved."
            )

        if assessment.energy.monthly_consumption_kwh is None:
            return self._insufficient(
                "The monthly consumption is not known (a bill-based estimate could not be made), "
                "so system coverage cannot be calculated."
            )

        profile = self._location_service.get_profile(
            float(assessment.location.latitude), float(assessment.location.longitude)
        )

        engine_input = SolarEngineInput(
            monthly_consumption_kwh=float(assessment.energy.monthly_consumption_kwh),
            roof_area_sqft=(
                float(assessment.constraints.roof_area_sqft)
                if assessment.constraints.roof_area_sqft is not None
                else None
            ),
            building_type=assessment.building.building_type,
            solar_resource=profile.solar,
        )

        result = run_solar_engine(engine_input)
        result = self._attach_context(result, assessment, profile)
        self._record_snapshot(assessment_id, engine_input, result)

        return result

    def _get_assessment(self, assessment_id: uuid.UUID) -> Assessment:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return assessment

    def _insufficient(self, reason: str) -> SolarCalculationResponse:
        return SolarCalculationResponse(
            status="insufficient_data",
            reason=reason,
            calculation_version=ENGINE_CALCULATION_VERSION,
            assumption_version=ASSUMPTION_VERSION,
            calculated_at=datetime.now(UTC),
        )

    def _attach_context(
        self, result: SolarCalculationResponse, assessment: Assessment, profile: LocationProfile
    ) -> SolarCalculationResponse:
        india = profile.india
        location_summary = SolarLocationSummary(
            latitude=profile.latitude,
            longitude=profile.longitude,
            formatted_address=profile.formatted_address,
            city=profile.city,
            district=india.district if india else None,
            state=india.state if india else None,
            union_territory=india.union_territory if india else None,
            country=assessment.location.country,
            discom_status=india.discom_status if india else "not_identified",
        )

        data_sources = []
        if profile.solar is not None:
            data_sources.append(
                SolarDataSource(
                    category="solar_resource",
                    provider=profile.solar.source,
                    unit=profile.solar.unit,
                    period_represented=profile.solar.period_represented,
                    retrieved_at=profile.solar.retrieved_at,
                )
            )
        data_sources.append(
            SolarDataSource(
                category="location",
                provider="Nominatim (OpenStreetMap)",
                retrieved_at=profile.retrieved_at,
            )
        )

        return result.model_copy(update={"location": location_summary, "data_sources": data_sources})

    def _record_snapshot(
        self, assessment_id: uuid.UUID, engine_input: SolarEngineInput, result: SolarCalculationResponse
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
            logger.exception("Failed to record solar calculation snapshot (best-effort, non-fatal)")
