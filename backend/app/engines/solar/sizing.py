"""Roof-area estimation and candidate-capacity evaluation.

Produces every candidate option (see assumptions.CANDIDATE_CAPACITIES_KW)
with its own technical_status — this module never picks a "best" or
"recommended" system. That comparison belongs to a future Recommendation
Engine, which does not exist yet.
"""

from app.engines.solar.assumptions import LAYOUT_FACTOR, PANEL_AREA_SQFT, PANEL_WATTAGE_W, PERFORMANCE_RATIO
from app.engines.solar.generation import estimate_annual_generation_kwh, estimate_monthly_generation_kwh
from app.engines.solar.validation import validate_capacity
from app.schemas.location import SolarResourceProfile
from app.schemas.solar import SolarSystemOption, TechnicalStatus


def estimate_roof_area_required_sqft(
    capacity_kw: float,
    panel_wattage_w: float = PANEL_WATTAGE_W.value,
    panel_area_sqft: float = PANEL_AREA_SQFT.value,
    layout_factor: float = LAYOUT_FACTOR.value,
) -> float:
    error = validate_capacity(capacity_kw)
    if error:
        raise ValueError(error)

    panels_needed = (capacity_kw * 1000) / panel_wattage_w
    return panels_needed * panel_area_sqft * layout_factor


def _determine_technical_status(
    roof_area_required_sqft: float, available_roof_area_sqft: float | None
) -> tuple[TechnicalStatus, list[str]]:
    if available_roof_area_sqft is None:
        return "insufficient_data", ["Roof area was not provided in the assessment."]
    if roof_area_required_sqft > available_roof_area_sqft:
        return "technically_infeasible", [
            f"Requires {roof_area_required_sqft:.0f} sq ft; only {available_roof_area_sqft:.0f} sq ft available."
        ]
    return "technically_feasible", []


def evaluate_candidate(
    capacity_kw: float,
    solar_resource: SolarResourceProfile,
    roof_area_sqft: float | None,
    annual_consumption_kwh: float,
) -> SolarSystemOption:
    annual_generation = estimate_annual_generation_kwh(capacity_kw, solar_resource.annual_value)
    monthly_generation = (
        estimate_monthly_generation_kwh(capacity_kw, solar_resource.monthly_values)
        if solar_resource.monthly_values
        else None
    )
    roof_area_required = estimate_roof_area_required_sqft(capacity_kw)
    coverage_percent = (
        round((annual_generation / annual_consumption_kwh) * 100, 1) if annual_consumption_kwh > 0 else None
    )
    status, notes = _determine_technical_status(roof_area_required, roof_area_sqft)

    return SolarSystemOption(
        capacity_kw=capacity_kw,
        estimated_annual_generation_kwh=round(annual_generation, 1),
        estimated_monthly_generation_kwh=(
            {month: round(value, 1) for month, value in monthly_generation.items()} if monthly_generation else None
        ),
        roof_area_required_sqft=round(roof_area_required, 1),
        generation_coverage_percent=coverage_percent,
        technical_status=status,
        technical_notes=notes,
    )


def evaluate_candidates(
    capacities_kw: list[float],
    solar_resource: SolarResourceProfile,
    roof_area_sqft: float | None,
    annual_consumption_kwh: float,
) -> list[SolarSystemOption]:
    return [
        evaluate_candidate(capacity_kw, solar_resource, roof_area_sqft, annual_consumption_kwh)
        for capacity_kw in capacities_kw
    ]
