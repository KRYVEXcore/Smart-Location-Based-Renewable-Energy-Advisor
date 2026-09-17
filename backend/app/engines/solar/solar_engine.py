"""Solar Engine entry point.

Pure calculation: takes a SolarEngineInput (assembled by
SolarCalculationService from an Assessment + the Phase 3 LocationProfile —
this module never touches the database, FastAPI, or a resource provider)
and returns a SolarCalculationResponse. `location` and `data_sources` are
left empty here; the service layer fills those in from data it already
holds, since the engine itself only knows about the resource value, not
the surrounding location/provider metadata.

No recommendation, subsidy, tariff, cost, saving, or payback is computed
here — see the README's Phase 4 boundary notes.
"""

from datetime import UTC, datetime

from app.engines.solar.assumptions import (
    ALL_ASSUMPTIONS,
    ASSUMPTION_VERSION,
    Assumption,
    CANDIDATE_CAPACITIES_KW,
    ENGINE_CALCULATION_VERSION,
)
from app.engines.solar.sizing import evaluate_candidates
from app.engines.solar.validation import validate_consumption, validate_solar_resource
from app.schemas.solar import SolarAssumptionOut, SolarCalculationResponse, SolarEngineInput


def calculate(engine_input: SolarEngineInput) -> SolarCalculationResponse:
    now = datetime.now(UTC)

    error = validate_consumption(engine_input.monthly_consumption_kwh) or validate_solar_resource(
        engine_input.solar_resource
    )
    if error:
        return _insufficient(error, now)

    solar_resource = engine_input.solar_resource
    assert solar_resource is not None  # validated above

    # 1 electricity unit = 1 kWh; monthly_consumption_kwh is already in kWh.
    annual_consumption_kwh = engine_input.monthly_consumption_kwh * 12

    options = evaluate_candidates(
        CANDIDATE_CAPACITIES_KW, solar_resource, engine_input.roof_area_sqft, annual_consumption_kwh
    )

    return SolarCalculationResponse(
        status="ok",
        consumer_category=engine_input.building_type,
        annual_consumption_kwh=round(annual_consumption_kwh, 1),
        options=options,
        assumptions=[_to_assumption_out(a) for a in ALL_ASSUMPTIONS],
        calculation_version=ENGINE_CALCULATION_VERSION,
        assumption_version=ASSUMPTION_VERSION,
        calculated_at=now,
    )


def _insufficient(reason: str, now: datetime) -> SolarCalculationResponse:
    return SolarCalculationResponse(
        status="insufficient_data",
        reason=reason,
        calculation_version=ENGINE_CALCULATION_VERSION,
        assumption_version=ASSUMPTION_VERSION,
        calculated_at=now,
    )


def _to_assumption_out(assumption: Assumption) -> SolarAssumptionOut:
    return SolarAssumptionOut(
        name=assumption.name,
        value=assumption.value,
        unit=assumption.unit,
        source=assumption.source,
        version=assumption.version,
        effective_from=assumption.effective_from,
        notes=assumption.notes,
    )
