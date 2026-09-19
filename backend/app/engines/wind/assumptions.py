"""Centralized, versioned wind screening assumptions.

Same rule as app.engines.solar.assumptions: every non-measured constant
lives here, named and labelled, never inline in a formula. Change a value
by adding a new dated version, not by editing calculation code.

EVERYTHING BELOW IS A MODEL ASSUMPTION. Nothing here is a measured value
for a site, and the turbine is a generic reference, not a real product.
"""

from dataclasses import dataclass

# Reuse Phase 4's calendar convention (non-leap year, 365 days) and the
# Assumption record so wind and solar report assumptions the same way.
from app.engines.solar.assumptions import DAYS_IN_MONTH, Assumption

ASSUMPTION_VERSION = "wind-assumptions-2026.1"
ENGINE_CALCULATION_VERSION = "wind-engine-2026.1"
METHODOLOGY = (
    "Generic reference power curve integrated over a Rayleigh (Weibull shape 2) wind-speed distribution "
    "whose mean is the Phase 3 monthly mean wind speed at the reference height; monthly energy = "
    "capacity x mean power fraction x hours in month x explicit loss factors."
)

# Phase 3 (NASA POWER WS10M / WS50M) reports wind speed in m/s. A resource in
# any other unit must not be run through these formulas unchanged.
SUPPORTED_WIND_UNIT = "m/s"

HOURS_PER_DAY = 24

# Candidate technical-analysis sizes, not universally suitable residential
# turbines. Configurable: pass another list to engine.calculate().
CANDIDATE_CAPACITIES_KW: list[float] = [0.5, 1, 2, 3, 5, 10]

VERSION_FIELDS = dict(version=ASSUMPTION_VERSION, effective_from="2026-01-01")

RESOURCE_REFERENCE_HEIGHT_M = Assumption(
    name="resource_reference_height_m",
    value=10.0,
    unit="m",
    source=(
        "Phase 3 provides only 10 m and 50 m wind speeds. The 10 m reading is used as-is as the wind at the "
        "turbine. No hub-height, roughness or obstruction correction is applied (none is invented)."
    ),
    notes=(
        "Real turbine hub heights and nearby buildings/trees can make the true site wind higher or, "
        "in built-up areas, much lower than this regional grid value."
    ),
    **VERSION_FIELDS,
)

WEIBULL_SHAPE = Assumption(
    name="weibull_shape_k",
    value=2.0,
    unit="ratio",
    source=(
        "Rayleigh distribution (Weibull shape 2), the conventional default when only a mean wind speed is "
        "known (as in IEC 61400-2 annual-energy estimates). Phase 3 supplies no speed distribution."
    ),
    notes="A screening assumption. A real site's distribution can differ and changes the result.",
    **VERSION_FIELDS,
)

TURBINE_AVAILABILITY = Assumption(
    name="turbine_availability",
    value=0.95,
    unit="ratio",
    source="Generic allowance for downtime/maintenance. An engineering assumption, not a measured value.",
    **VERSION_FIELDS,
)

ELECTRICAL_LOSSES = Assumption(
    name="electrical_and_other_efficiency",
    value=0.95,
    unit="ratio",
    source="Generic allowance for generator, inverter and cable losses. An engineering assumption.",
    **VERSION_FIELDS,
)

FEASIBLE_MIN_NET_CAPACITY_FACTOR = Assumption(
    name="feasible_min_net_capacity_factor",
    value=0.15,
    unit="ratio",
    source="Screening threshold chosen for this prototype. NOT a government or industry standard.",
    **VERSION_FIELDS,
)

MARGINAL_MIN_NET_CAPACITY_FACTOR = Assumption(
    name="marginal_min_net_capacity_factor",
    value=0.08,
    unit="ratio",
    source="Screening threshold chosen for this prototype. NOT a government or industry standard.",
    **VERSION_FIELDS,
)


@dataclass(frozen=True)
class TurbineModel:
    """Generic reference turbine. `curve` is (wind speed m/s, fraction of rated power)."""

    name: str
    cut_in_speed_mps: float
    rated_speed_mps: float
    cut_out_speed_mps: float
    curve: tuple[tuple[float, float], ...]


# Idealised curve: 0 below cut-in, output rising with the cube of wind speed
# between cut-in and rated speed, P/Prated = (v^3 - vci^3) / (vr^3 - vci^3),
# then flat at rated output up to cut-out; 0 above cut-out. Points are the
# formula at 1 m/s steps, rounded to 4 places, and are linearly interpolated.
# Speeds exactly at cut-in give 0; speeds up to and including cut-out give
# the curve value; speeds above cut-out give 0.
GENERIC_REFERENCE_TURBINE = TurbineModel(
    name="GENERIC-REFERENCE-SMALL-WIND (model assumption, not a real product)",
    cut_in_speed_mps=3.0,
    rated_speed_mps=11.0,
    cut_out_speed_mps=25.0,
    curve=(
        (0.0, 0.0),
        (3.0, 0.0),
        (4.0, 0.0284),
        (5.0, 0.0752),
        (6.0, 0.1449),
        (7.0, 0.2423),
        (8.0, 0.3719),
        (9.0, 0.5383),
        (10.0, 0.7462),
        (11.0, 1.0),
        (25.0, 1.0),
    ),
)

ALL_ASSUMPTIONS: list[Assumption] = [
    RESOURCE_REFERENCE_HEIGHT_M,
    WEIBULL_SHAPE,
    TURBINE_AVAILABILITY,
    ELECTRICAL_LOSSES,
    FEASIBLE_MIN_NET_CAPACITY_FACTOR,
    MARGINAL_MIN_NET_CAPACITY_FACTOR,
]

DATA_TYPE = "Regional climatology model value (NASA POWER, 2001-2020 average). Not a live or on-site measurement."

LIMITATIONS: list[str] = [
    "Technical screening only. Structural, zoning, noise, vibration and installation approval are required "
    "before any turbine is considered.",
    "The wind speed is a regional model value for a grid cell, not an anemometer reading at the site. "
    "Urban turbulence and obstructions can make real wind much poorer.",
    "The 10 m wind speed is used as the wind at the turbine; hub height is not modelled.",
    "Air-density (altitude/temperature) effects and the site's real wind-speed distribution are not modelled.",
    "The turbine is a generic reference, not a real product. This is not a recommendation.",
    "No cost, subsidy, savings or payback is calculated in this phase.",
]

__all__ = [
    "ALL_ASSUMPTIONS",
    "ASSUMPTION_VERSION",
    "CANDIDATE_CAPACITIES_KW",
    "DAYS_IN_MONTH",
    "DATA_TYPE",
    "ENGINE_CALCULATION_VERSION",
    "GENERIC_REFERENCE_TURBINE",
    "HOURS_PER_DAY",
    "LIMITATIONS",
    "METHODOLOGY",
    "SUPPORTED_WIND_UNIT",
    "TurbineModel",
]
