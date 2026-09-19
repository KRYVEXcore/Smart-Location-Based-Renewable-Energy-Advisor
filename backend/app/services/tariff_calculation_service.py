import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.repositories.assessment_repository import AssessmentRepository
from app.database.repositories.tariff_calculation_snapshot_repository import (
    TariffCalculationSnapshotRepository,
)
from app.database.repositories.tariff_repository import TariffRepository
from app.engines.tariff.consumer_category_mapping import map_building_type_to_consumer_category
from app.engines.tariff.tariff_engine import calculate_bill_for_grid_consumption
from app.engines.tariff.version import ENGINE_CALCULATION_VERSION
from app.models.assessment import Assessment
from app.models.electricity_tariff import ElectricityTariff
from app.models.enums import TariffConsumerCategory
from app.schemas.location import IndiaLocationContext, LocationProfile
from app.schemas.tariff import TariffCalculationResponse, TariffLocationSummary, TariffSlabInput
from app.services.location.location_service import LocationService

logger = logging.getLogger(__name__)


class TariffCalculationService:
    """Orchestrates: Assessment -> Phase 3 LocationProfile (India context) ->
    consumer-category mapping -> tariff row lookup -> Tariff Engine ->
    response, and records a reproducibility snapshot. Contains no tariff
    calculation logic itself — see app.engines.tariff for that.

    Never re-derives location or DISCOM resolution — both come from the
    existing Phase 3 LocationService / India resolver.
    """

    def __init__(self, db: Session, location_service: LocationService) -> None:
        self.db = db
        self._location_service = location_service
        self._assessments = AssessmentRepository(db)
        self._tariffs = TariffRepository(db)
        self._snapshots = TariffCalculationSnapshotRepository(db)

    def calculate_for_assessment(
        self, assessment_id: uuid.UUID, calculation_date: date | None = None
    ) -> TariffCalculationResponse:
        assessment = self._get_assessment(assessment_id)
        calc_date = calculation_date or date.today()

        if assessment.location.latitude is None or assessment.location.longitude is None:
            return self._insufficient(
                "This assessment has no saved coordinates, so its location cannot be resolved."
            )

        profile = self._location_service.get_profile(
            float(assessment.location.latitude), float(assessment.location.longitude)
        )
        india = profile.india

        if india is None or (india.state is None and india.union_territory is None):
            return self._insufficient(
                "This location could not be resolved to an Indian state or union territory, "
                "so no tariff can be looked up.",
                profile=profile,
            )

        consumer_category = map_building_type_to_consumer_category(assessment.building.building_type)
        rows = self._tariffs.find_candidates(
            state=india.state, union_territory=india.union_territory, consumer_category=consumer_category
        )
        scoped_rows = self._scope_by_discom(rows, india)

        if not scoped_rows:
            if india.discom_status == "ambiguous":
                return self._discom_ambiguous(profile, india, consumer_category)
            return self._tariff_not_configured(profile, india, consumer_category, calc_date)

        consumption_kwh = _to_decimal(assessment.energy.monthly_consumption_kwh)
        slab_inputs = [_to_slab_input(row) for row in scoped_rows]

        result = calculate_bill_for_grid_consumption(consumption_kwh, slab_inputs, calc_date, consumer_category)
        result = self._attach_location(result, profile, india)
        self._record_snapshot(assessment_id, consumption_kwh, calc_date, consumer_category, result)

        return result

    def _get_assessment(self, assessment_id: uuid.UUID) -> Assessment:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return assessment

    def _scope_by_discom(
        self, rows: list[ElectricityTariff], india: IndiaLocationContext
    ) -> list[ElectricityTariff]:
        state_level = [row for row in rows if row.discom_id is None]

        if india.discom_status == "identified" and india.discom is not None:
            discom_specific = [
                row for row in rows if row.discom_id is not None and str(row.discom_id) == india.discom.id
            ]
            # Prefer the exact DISCOM's tariff; fall back to a state-level
            # tariff only if that DISCOM has none configured.
            return discom_specific or state_level

        # "ambiguous" or "not_identified": never guess which DISCOM applies —
        # only a tariff explicitly scoped to the whole state/UT (no specific
        # DISCOM) may be used.
        return state_level

    def _insufficient(self, reason: str, profile: LocationProfile | None = None) -> TariffCalculationResponse:
        return TariffCalculationResponse(
            status="insufficient_data",
            reason=reason,
            location=self._location_summary(profile, profile.india if profile else None) if profile else None,
            calculation_version=ENGINE_CALCULATION_VERSION,
            calculated_at=datetime.now(UTC),
        )

    def _discom_ambiguous(
        self,
        profile: LocationProfile,
        india: IndiaLocationContext,
        consumer_category: TariffConsumerCategory,
    ) -> TariffCalculationResponse:
        return TariffCalculationResponse(
            status="discom_ambiguous",
            reason=(
                "More than one electricity distribution company matches this location, so the "
                "applicable tariff cannot be determined without guessing. No state-level tariff "
                "is configured as a fallback."
            ),
            location=self._location_summary(profile, india),
            consumer_category=consumer_category,
            calculation_version=ENGINE_CALCULATION_VERSION,
            calculated_at=datetime.now(UTC),
        )

    def _tariff_not_configured(
        self,
        profile: LocationProfile,
        india: IndiaLocationContext,
        consumer_category: TariffConsumerCategory,
        calc_date: date,
    ) -> TariffCalculationResponse:
        place = india.state or india.union_territory
        return TariffCalculationResponse(
            status="tariff_not_configured",
            reason=(
                f"No verified electricity tariff is configured for {place} "
                f"({consumer_category.value}) as of {calc_date.isoformat()}."
            ),
            location=self._location_summary(profile, india),
            consumer_category=consumer_category,
            calculation_version=ENGINE_CALCULATION_VERSION,
            calculated_at=datetime.now(UTC),
        )

    def _location_summary(
        self, profile: LocationProfile | None, india: IndiaLocationContext | None
    ) -> TariffLocationSummary | None:
        if profile is None:
            return None
        return TariffLocationSummary(
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

    def _attach_location(
        self, result: TariffCalculationResponse, profile: LocationProfile, india: IndiaLocationContext
    ) -> TariffCalculationResponse:
        return result.model_copy(update={"location": self._location_summary(profile, india)})

    def _record_snapshot(
        self,
        assessment_id: uuid.UUID,
        consumption_kwh: Decimal,
        calc_date: date,
        consumer_category: TariffConsumerCategory,
        result: TariffCalculationResponse,
    ) -> None:
        try:
            self._snapshots.record(
                assessment_id=assessment_id,
                calculation_version=result.calculation_version,
                input_snapshot={
                    "monthly_consumption_kwh": str(consumption_kwh),
                    "calculation_date": calc_date.isoformat(),
                    "consumer_category": consumer_category.value,
                },
                result_snapshot=result.model_dump(mode="json"),
            )
            self.db.commit()
        except Exception:
            logger.exception("Failed to record tariff calculation snapshot (best-effort, non-fatal)")


def _to_decimal(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _to_decimal_or_none(value: object | None) -> Decimal | None:
    return None if value is None else _to_decimal(value)


def _to_slab_input(row: ElectricityTariff) -> TariffSlabInput:
    return TariffSlabInput(
        tariff_version=row.tariff_version,
        tariff_name=row.tariff_name,
        slab_min_kwh=_to_decimal(row.slab_min_kwh),
        slab_max_kwh=_to_decimal_or_none(row.slab_max_kwh),
        energy_charge_inr_per_kwh=_to_decimal(row.energy_charge_inr_per_kwh),
        fixed_charge_inr=_to_decimal_or_none(row.fixed_charge_inr),
        fixed_charge_basis=row.fixed_charge_basis,
        demand_charge_inr=_to_decimal_or_none(row.demand_charge_inr),
        wheeling_charge_inr_per_kwh=_to_decimal_or_none(row.wheeling_charge_inr_per_kwh),
        effective_from=row.effective_from,
        effective_to=row.effective_to,
        source_url=row.source_url,
        source_document=row.source_document,
        source_name=row.source_name,
        source_order_number=row.source_order_number,
        source_order_date=row.source_order_date,
        source_page=row.source_page,
        source_table=row.source_table,
        source_section=row.source_section,
        source_excerpt=row.source_excerpt,
        verification_notes=row.verification_notes,
        last_verified=row.last_verified,
        verification_status=row.verification_status,
        discom_id=row.discom_id,
    )
