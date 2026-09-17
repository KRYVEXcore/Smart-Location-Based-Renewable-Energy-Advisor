"""Deterministic solar generation formulas.

Standard rooftop-PV energy yield estimation:

    Annual Generation (kWh) = Capacity (kWp) x Daily Solar Resource (kWh/m^2/day) x 365 x Performance Ratio

The daily solar resource value (kWh/m^2/day, from NASA POWER's
ALLSKY_SFC_SW_DWN via app.services.location) is numerically equivalent to
"peak sun hours per day", which is what this formula expects — this is the
same method used by widely-referenced PV estimation tools (e.g. NREL's
PVWatts methodology). See app.engines.solar.assumptions for the Performance
Ratio's value and source; nothing here is measured for a specific site.

Monthly generation uses the same formula per month, with that month's
average daily resource value and its real number of calendar days —
never a naive annual/12 split.
"""

from app.engines.solar.assumptions import DAYS_IN_MONTH, DAYS_PER_YEAR, PERFORMANCE_RATIO
from app.engines.solar.validation import validate_capacity


def estimate_annual_generation_kwh(
    capacity_kw: float, daily_solar_resource_kwh_per_m2: float, performance_ratio: float = PERFORMANCE_RATIO.value
) -> float:
    error = validate_capacity(capacity_kw)
    if error:
        raise ValueError(error)
    return capacity_kw * daily_solar_resource_kwh_per_m2 * DAYS_PER_YEAR * performance_ratio


def estimate_monthly_generation_kwh(
    capacity_kw: float,
    monthly_daily_avg_resource: dict[str, float],
    performance_ratio: float = PERFORMANCE_RATIO.value,
) -> dict[str, float]:
    error = validate_capacity(capacity_kw)
    if error:
        raise ValueError(error)

    return {
        month: capacity_kw * daily_avg * DAYS_IN_MONTH[month] * performance_ratio
        for month, daily_avg in monthly_daily_avg_resource.items()
        if month in DAYS_IN_MONTH
    }
