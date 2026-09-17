"""Centralized, versioned solar engineering assumptions.

Every non-measured constant the Solar Engine uses lives here, named,
sourced, and versioned — never inline in a calculation function. Bumping
ASSUMPTION_VERSION (and adding a new dated entry, keeping the old one for
reproducibility of past calculations) is how these change over time;
calculation logic in generation.py/sizing.py never changes to reflect a
new assumption value.

These are standard rooftop-PV engineering approximations, not measured
empirical data for any specific site — each `source` string says so
explicitly rather than implying false precision.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Assumption:
    name: str
    value: float
    unit: str
    source: str
    version: str
    effective_from: str
    notes: str = ""


ASSUMPTION_VERSION = "solar-assumptions-2026.1"

DAYS_PER_YEAR = 365

# Calendar days per month (non-leap year) — used to convert NASA POWER's
# monthly *daily-average* solar resource into a monthly generation total.
DAYS_IN_MONTH: dict[str, int] = {
    "JAN": 31,
    "FEB": 28,
    "MAR": 31,
    "APR": 30,
    "MAY": 31,
    "JUN": 30,
    "JUL": 31,
    "AUG": 31,
    "SEP": 30,
    "OCT": 31,
    "NOV": 30,
    "DEC": 31,
}

# The only solar-resource unit this engine knows how to interpret. NASA
# POWER's ALLSKY_SFC_SW_DWN (see app/services/location/providers/nasa_power.py)
# reports kWh/m^2/day, which is numerically equivalent to "peak sun hours per
# day" — directly usable in the standard kWp x PSH x PR yield formula. A
# resource in any other unit must not be fed through this formula unchanged.
SUPPORTED_SOLAR_RESOURCE_UNIT = "kWh/m^2/day"

PERFORMANCE_RATIO = Assumption(
    name="performance_ratio",
    value=0.75,
    unit="ratio",
    source=(
        "Conservative default for grid-connected rooftop PV performance ratio "
        "under Indian climate conditions (typical published range ~0.70-0.85), "
        "covering inverter, wiring, soiling, and temperature derating losses. "
        "Not a site-measured value."
    ),
    version=ASSUMPTION_VERSION,
    effective_from="2026-01-01",
    notes="Applied uniformly to annual and monthly generation estimates.",
)

PANEL_WATTAGE_W = Assumption(
    name="panel_wattage_w",
    value=400.0,
    unit="W",
    source="Representative modern monocrystalline PERC rooftop module rating (commonly 380-450W).",
    version=ASSUMPTION_VERSION,
    effective_from="2026-01-01",
    notes="Used only to derive roof area required — does not affect the generation estimate.",
)

PANEL_AREA_SQFT = Assumption(
    name="panel_area_sqft",
    value=21.0,
    unit="sqft",
    source="Typical physical footprint of a ~400W monocrystalline panel (~1.95m x 1.0m).",
    version=ASSUMPTION_VERSION,
    effective_from="2026-01-01",
)

LAYOUT_FACTOR = Assumption(
    name="layout_factor",
    value=1.4,
    unit="ratio",
    source=(
        "Typical allowance for mounting-structure spacing, walkways, and "
        "shading clearance on Indian rooftops — a rule-of-thumb multiplier "
        "on raw panel area, not a site survey."
    ),
    version=ASSUMPTION_VERSION,
    effective_from="2026-01-01",
)

CANDIDATE_CAPACITIES_KW: list[float] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

ENGINE_CALCULATION_VERSION = "solar-engine-2026.1"

ALL_ASSUMPTIONS: list[Assumption] = [
    PERFORMANCE_RATIO,
    PANEL_WATTAGE_W,
    PANEL_AREA_SQFT,
    LAYOUT_FACTOR,
]
