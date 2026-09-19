"""Deterministic wind power-curve and energy-yield calculation.

Not `capacity x mean wind speed`: turbine output is a non-linear function of
wind speed (cut-in, cubic ramp, rated plateau, cut-out), so the power curve
is averaged over the wind-speed distribution implied by the mean speed.
Pure functions, stdlib only.
"""

import math
from dataclasses import dataclass

from app.engines.solar.validation import validate_capacity
from app.engines.wind.assumptions import (
    DAYS_IN_MONTH,
    ELECTRICAL_LOSSES,
    GENERIC_REFERENCE_TURBINE,
    HOURS_PER_DAY,
    TURBINE_AVAILABILITY,
    WEIBULL_SHAPE,
    TurbineModel,
)

BIN_WIDTH_MPS = 0.25
HOURS_PER_YEAR = 365 * HOURS_PER_DAY  # same non-leap calendar as the solar engine


def validate_power_curve(turbine: TurbineModel) -> str | None:
    """Returns a failure reason, or None if the curve is a valid turbine model."""
    curve = turbine.curve
    if len(curve) < 2:
        return "Power curve needs at least two points."
    speeds = [speed for speed, _ in curve]
    for previous, current in zip(speeds, speeds[1:]):
        if current == previous:
            return f"Duplicate power-curve point at {current} m/s."
        if current < previous:
            return f"Power-curve wind speeds must be ascending ({previous} then {current})."
    if speeds[0] != 0:
        return "Power curve must start at 0 m/s."
    if not turbine.cut_in_speed_mps < turbine.rated_speed_mps < turbine.cut_out_speed_mps:
        return "Speeds must satisfy cut-in < rated < cut-out."
    if speeds[-1] != turbine.cut_out_speed_mps:
        return "Power curve must end at the cut-out speed."
    fractions = [fraction for _, fraction in curve]
    if any(fraction < 0 for fraction in fractions):
        return "Power curve has negative output."
    if any(fraction > 1 for fraction in fractions):
        return "Power curve output exceeds rated capacity."
    if any(later < earlier for earlier, later in zip(fractions, fractions[1:])):
        return "Power curve output must not decrease before cut-out."
    return None


def power_fraction(wind_speed_mps: float, turbine: TurbineModel = GENERIC_REFERENCE_TURBINE) -> float:
    """Output as a fraction of rated power (0..1) at a wind speed.

    0 at or below cut-in; interpolated between curve points; rated up to and
    including cut-out; 0 above cut-out. Never extrapolated.
    """
    if wind_speed_mps < 0:
        raise ValueError(f"Wind speed cannot be negative: {wind_speed_mps}")
    if wind_speed_mps <= turbine.cut_in_speed_mps or wind_speed_mps > turbine.cut_out_speed_mps:
        return 0.0
    for (v0, p0), (v1, p1) in zip(turbine.curve, turbine.curve[1:]):
        if v0 <= wind_speed_mps <= v1:
            return p0 + (p1 - p0) * (wind_speed_mps - v0) / (v1 - v0)
    return 0.0  # unreachable for a validated curve


def mean_power_fraction(
    mean_speed_mps: float, turbine: TurbineModel = GENERIC_REFERENCE_TURBINE, shape: float = WEIBULL_SHAPE.value
) -> float:
    """Expected fraction of rated power for a Weibull(shape) wind whose mean is mean_speed_mps."""
    if mean_speed_mps <= 0:
        raise ValueError(f"Mean wind speed must be greater than 0: {mean_speed_mps}")
    scale = mean_speed_mps / math.gamma(1 + 1 / shape)

    def cdf(speed: float) -> float:
        return 1 - math.exp(-((speed / scale) ** shape))

    bins = round(turbine.cut_out_speed_mps / BIN_WIDTH_MPS)
    total = 0.0
    for i in range(bins):
        low, high = i * BIN_WIDTH_MPS, (i + 1) * BIN_WIDTH_MPS
        total += (cdf(high) - cdf(low)) * power_fraction((low + high) / 2, turbine)
    return total


@dataclass(frozen=True)
class WindGeneration:
    annual_generation_kwh: float
    monthly_generation_kwh: dict[str, float] | None
    net_capacity_factor: float
    equivalent_full_load_hours: float


def calculate_annual_wind_generation(
    capacity_kw: float,
    annual_mean_speed_mps: float,
    monthly_mean_speeds_mps: dict[str, float] | None = None,
    turbine: TurbineModel = GENERIC_REFERENCE_TURBINE,
) -> WindGeneration:
    """Annual (and, when all 12 monthly means are present, monthly) energy.

    With monthly means, each month uses its own mean speed and real day
    count and the annual figure is their sum. Otherwise the annual mean
    speed is used for the whole year. Monthly values are never invented.
    """
    error = validate_capacity(capacity_kw)
    if error:
        raise ValueError(error)
    if (error := validate_power_curve(turbine)) is not None:
        raise ValueError(error)

    losses = TURBINE_AVAILABILITY.value * ELECTRICAL_LOSSES.value
    has_monthly = bool(monthly_mean_speeds_mps) and all(m in monthly_mean_speeds_mps for m in DAYS_IN_MONTH)

    monthly: dict[str, float] | None = None
    if has_monthly:
        monthly = {
            month: capacity_kw
            * mean_power_fraction(monthly_mean_speeds_mps[month], turbine)
            * HOURS_PER_DAY
            * days
            * losses
            for month, days in DAYS_IN_MONTH.items()
        }
        annual = sum(monthly.values())
    else:
        annual = capacity_kw * mean_power_fraction(annual_mean_speed_mps, turbine) * HOURS_PER_YEAR * losses

    return WindGeneration(
        annual_generation_kwh=annual,
        monthly_generation_kwh=monthly,
        net_capacity_factor=annual / (capacity_kw * HOURS_PER_YEAR),
        equivalent_full_load_hours=annual / capacity_kw,
    )
