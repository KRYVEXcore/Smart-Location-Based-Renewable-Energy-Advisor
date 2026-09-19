"""Wind Engine entry point.

Pure calculation: takes a WindEngineInput (assembled by
WindCalculationService from an Assessment + the Phase 3 LocationProfile)
and returns a WindCalculationResponse. It never calls a provider, the
database or FastAPI, and never invents a wind speed: a missing or unusable
resource yields a status, not a default.

No recommendation, cost, subsidy, saving or payback is computed here.
"""

from datetime import UTC, datetime

from app.engines.solar.validation import validate_capacity
from app.engines.wind.assumptions import (
    ALL_ASSUMPTIONS,
    ASSUMPTION_VERSION,
    CANDIDATE_CAPACITIES_KW,
    DATA_TYPE,
    ENGINE_CALCULATION_VERSION,
    FEASIBLE_MIN_NET_CAPACITY_FACTOR,
    GENERIC_REFERENCE_TURBINE,
    LIMITATIONS,
    MARGINAL_MIN_NET_CAPACITY_FACTOR,
    METHODOLOGY,
    RESOURCE_REFERENCE_HEIGHT_M,
    SUPPORTED_WIND_UNIT,
)
from app.engines.wind.generation import calculate_annual_wind_generation
from app.schemas.location import WindResourceProfile, WindSpeedReading
from app.schemas.solar import SolarAssumptionOut
from app.schemas.wind import (
    WindCalculationResponse,
    WindCandidate,
    WindCandidateStatus,
    WindEngineInput,
    WindReadingOut,
    WindResourceOut,
    WindTurbineOut,
)

SITE_SPACE_UNKNOWN = "Site-space requirement cannot yet be fully evaluated."


def select_reading(wind_resource: WindResourceProfile) -> WindSpeedReading | None:
    for reading in wind_resource.readings:
        if reading.reference_height_m == RESOURCE_REFERENCE_HEIGHT_M.value:
            return reading
    return None


def validate_reading(reading: WindSpeedReading | None) -> str | None:
    """Returns why a resource cannot be used, or None if it can."""
    if reading is None:
        return f"No wind reading at the {RESOURCE_REFERENCE_HEIGHT_M.value:g} m reference height."
    if reading.unit != SUPPORTED_WIND_UNIT:
        return f"Unsupported wind unit {reading.unit!r}; this engine only interprets {SUPPORTED_WIND_UNIT!r}."
    if reading.annual_value is None:
        return "The wind reading has no usable annual value."
    if reading.annual_value <= 0:
        return f"The annual mean wind speed is non-positive ({reading.annual_value} m/s)."
    if reading.monthly_values and any(value <= 0 for value in reading.monthly_values.values()):
        return "The wind reading has a non-positive monthly value."
    return None


def candidate_status(net_capacity_factor: float) -> tuple[WindCandidateStatus, list[str]]:
    feasible, marginal = FEASIBLE_MIN_NET_CAPACITY_FACTOR.value, MARGINAL_MIN_NET_CAPACITY_FACTOR.value
    if net_capacity_factor >= feasible:
        return "technically_feasible", [f"Net capacity factor is at or above the {feasible:.0%} screening threshold."]
    if net_capacity_factor >= marginal:
        return "marginal", [f"Net capacity factor is between the {marginal:.0%} and {feasible:.0%} screening thresholds."]
    return "insufficient_resource", [f"Net capacity factor is below the {marginal:.0%} screening threshold."]


def site_space_note(roof_area_sqft: float | None, land_area_sqft: float | None) -> str:
    provided = [
        f"{label} {area:,.0f} sq ft"
        for label, area in (("roof", roof_area_sqft), ("land", land_area_sqft))
        if area is not None
    ]
    if not provided:
        return SITE_SPACE_UNKNOWN
    return (
        f"Site-space information available ({', '.join(provided)}). Turbine footprint, clearance, mounting "
        "height and structural suitability are not evaluated."
    )


def calculate(
    engine_input: WindEngineInput, capacities_kw: list[float] | None = None
) -> WindCalculationResponse:
    now = datetime.now(UTC)
    capacities = CANDIDATE_CAPACITIES_KW if capacities_kw is None else capacities_kw
    for capacity in capacities:
        if (error := validate_capacity(capacity)) is not None:
            raise ValueError(error)

    if engine_input.wind_resource is None:
        return _failure("wind_resource_unavailable", "No verified wind resource is available for this location.", now)

    reading = select_reading(engine_input.wind_resource)
    if (error := validate_reading(reading)) is not None:
        return _failure("insufficient_data", error, now)
    assert reading is not None and reading.annual_value is not None  # validated above

    monthly = reading.monthly_values
    candidates = []
    used_monthly = False
    for capacity in capacities:
        generation = calculate_annual_wind_generation(capacity, reading.annual_value, monthly)
        used_monthly = generation.monthly_generation_kwh is not None
        status, notes = candidate_status(generation.net_capacity_factor)
        candidates.append(
            WindCandidate(
                capacity_kw=capacity,
                annual_generation_kwh=round(generation.annual_generation_kwh, 1),
                monthly_generation_kwh=(
                    {m: round(v, 1) for m, v in generation.monthly_generation_kwh.items()}
                    if generation.monthly_generation_kwh
                    else None
                ),
                net_capacity_factor=round(generation.net_capacity_factor, 4),
                equivalent_full_load_hours=round(generation.equivalent_full_load_hours, 1),
                technical_status=status,
                technical_notes=notes,
            )
        )

    return WindCalculationResponse(
        status="ok",
        resource=WindResourceOut(
            provider=engine_input.wind_resource.source,
            period_represented=engine_input.wind_resource.period_represented,
            retrieved_at=engine_input.wind_resource.retrieved_at,
            data_type=DATA_TYPE,
            readings=[
                WindReadingOut(
                    reference_height_m=r.reference_height_m,
                    annual_value=r.annual_value,
                    monthly_values=r.monthly_values,
                    unit=r.unit,
                )
                for r in engine_input.wind_resource.readings
            ],
            used_reference_height_m=reading.reference_height_m,
            used_annual_mean_speed_mps=reading.annual_value,
            used_monthly_means=used_monthly,
        ),
        turbine_model=WindTurbineOut(
            name=GENERIC_REFERENCE_TURBINE.name,
            cut_in_speed_mps=GENERIC_REFERENCE_TURBINE.cut_in_speed_mps,
            rated_speed_mps=GENERIC_REFERENCE_TURBINE.rated_speed_mps,
            cut_out_speed_mps=GENERIC_REFERENCE_TURBINE.cut_out_speed_mps,
            power_curve=list(GENERIC_REFERENCE_TURBINE.curve),
        ),
        candidates=candidates,
        site_space_note=site_space_note(engine_input.roof_area_sqft, engine_input.land_area_sqft),
        assumptions=[
            SolarAssumptionOut(
                name=a.name, value=a.value, unit=a.unit, source=a.source, version=a.version,
                effective_from=a.effective_from, notes=a.notes,
            )
            for a in ALL_ASSUMPTIONS
        ],
        limitations=LIMITATIONS,
        methodology=METHODOLOGY,
        calculation_version=ENGINE_CALCULATION_VERSION,
        assumption_version=ASSUMPTION_VERSION,
        calculated_at=now,
    )


def _failure(status: str, reason: str, now: datetime) -> WindCalculationResponse:
    return WindCalculationResponse(
        status=status,
        reason=reason,
        limitations=LIMITATIONS,
        calculation_version=ENGINE_CALCULATION_VERSION,
        assumption_version=ASSUMPTION_VERSION,
        calculated_at=now,
    )
