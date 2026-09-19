"""Wind power curve and generation math. Every wind speed below is a
TEST FIXTURE ONLY value used to exercise formulas, never real resource data.
"""

import math
from dataclasses import replace

import pytest

from app.engines.wind.assumptions import (
    DAYS_IN_MONTH,
    ELECTRICAL_LOSSES,
    GENERIC_REFERENCE_TURBINE as TURBINE,
    TURBINE_AVAILABILITY,
)
from app.engines.wind.generation import (
    HOURS_PER_YEAR,
    calculate_annual_wind_generation,
    mean_power_fraction,
    power_fraction,
    validate_power_curve,
)

LOSSES = TURBINE_AVAILABILITY.value * ELECTRICAL_LOSSES.value


# ------------------------------------------------------------ power curve


def test_the_reference_power_curve_is_valid():
    assert validate_power_curve(TURBINE) is None


def test_the_curve_points_follow_the_documented_cubic_ramp():
    vci, vr = TURBINE.cut_in_speed_mps, TURBINE.rated_speed_mps
    for speed, fraction in TURBINE.curve:
        if vci <= speed <= vr:
            assert fraction == pytest.approx((speed**3 - vci**3) / (vr**3 - vci**3), abs=5e-5)


@pytest.mark.parametrize(
    "speed, expected",
    [
        (0.0, 0.0),  # zero wind
        (1.0, 0.0),  # very low wind
        (2.999, 0.0),  # just below cut-in
        (3.0, 0.0),  # exactly cut-in
        (3.5, 0.0142),  # interpolated: halfway between (3, 0) and (4, 0.0284)
        (4.0, 0.0284),  # a curve point
        (7.5, 0.3071),  # interpolated between (7, .2423) and (8, .3719)
        (11.0, 1.0),  # exactly rated speed
        (18.0, 1.0),  # between rated and cut-out
        (25.0, 1.0),  # exactly cut-out (inclusive)
        (25.001, 0.0),  # just above cut-out
        (60.0, 0.0),  # very high wind: never extrapolated
    ],
)
def test_power_fraction_at_each_region_of_the_curve(speed, expected):
    assert power_fraction(speed) == pytest.approx(expected, abs=1e-4)


def test_power_fraction_is_never_negative_or_above_rated_and_never_decreases_before_cut_out():
    speeds = [i / 10 for i in range(0, 300)]
    values = [power_fraction(s) for s in speeds]
    assert all(0.0 <= v <= 1.0 for v in values)
    below_cut_out = [v for s, v in zip(speeds, values) if s <= TURBINE.cut_out_speed_mps]
    assert below_cut_out == sorted(below_cut_out)


def test_a_negative_wind_speed_is_rejected():
    with pytest.raises(ValueError):
        power_fraction(-0.1)


# ------------------------------------------------------- curve validation


def _with_curve(*points):
    return replace(TURBINE, curve=tuple(points))


@pytest.mark.parametrize(
    "curve, message",
    [
        (((0.0, 0.0),), "at least two"),
        (((0.0, 0.0), (3.0, 0.0), (3.0, 0.1), (25.0, 1.0)), "Duplicate"),
        (((0.0, 0.0), (5.0, 0.1), (4.0, 0.2), (25.0, 1.0)), "ascending"),
        (((0.0, 0.0), (3.0, -0.1), (11.0, 1.0), (25.0, 1.0)), "negative"),
        (((0.0, 0.0), (11.0, 1.2), (25.0, 1.2)), "exceeds rated"),
        (((0.0, 0.0), (11.0, 1.0), (18.0, 0.9), (25.0, 0.9)), "must not decrease"),
        (((1.0, 0.0), (11.0, 1.0), (25.0, 1.0)), "start at 0"),
        (((0.0, 0.0), (11.0, 1.0), (20.0, 1.0)), "end at the cut-out"),
    ],
)
def test_an_invalid_power_curve_is_rejected(curve, message):
    assert message in validate_power_curve(_with_curve(*curve))


def test_speeds_must_be_ordered_cut_in_rated_cut_out():
    assert "cut-in < rated < cut-out" in validate_power_curve(replace(TURBINE, cut_in_speed_mps=12.0))


def test_generation_refuses_an_invalid_turbine_model():
    bad = _with_curve((0.0, 0.0), (11.0, 1.4), (25.0, 1.4))
    with pytest.raises(ValueError, match="exceeds rated"):
        calculate_annual_wind_generation(1, 5.0, turbine=bad)


# --------------------------------------------------- distribution average


def _reference_mean_fraction(mean_speed: float, step: float = 0.005) -> float:
    """Independent fine-grained numerical integral of power x Rayleigh pdf."""
    scale = mean_speed / math.gamma(1.5)
    total, v = 0.0, step / 2
    while v < 30:
        pdf = (2 * v / scale**2) * math.exp(-((v / scale) ** 2))
        total += pdf * power_fraction(v) * step
        v += step
    return total


@pytest.mark.parametrize("mean_speed", [2.0, 3.5, 5.0, 6.5, 8.0])
def test_mean_power_fraction_matches_an_independent_integral(mean_speed):
    assert mean_power_fraction(mean_speed) == pytest.approx(_reference_mean_fraction(mean_speed), abs=2e-3)


def test_mean_power_fraction_is_bounded_and_rises_with_the_mean_speed_in_the_normal_range():
    values = [mean_power_fraction(s / 2) for s in range(2, 17)]  # 1.0 .. 8.0 m/s
    assert all(0.0 <= v <= 1.0 for v in values)
    assert values == sorted(values)


def test_mean_power_fraction_is_not_the_power_curve_at_the_mean_speed():
    # The whole point of integrating over the distribution: at a 4 m/s mean
    # the curve alone gives 2.84% but real winds spend time both above and below.
    assert mean_power_fraction(4.0) > power_fraction(4.0)


@pytest.mark.parametrize("bad", [0, -1.0])
def test_zero_or_negative_mean_wind_is_rejected(bad):
    with pytest.raises(ValueError):
        mean_power_fraction(bad)


# --------------------------------------------------------------- generation


@pytest.mark.parametrize("capacity", [0, -1, -0.5])
def test_zero_or_negative_capacity_is_rejected(capacity):
    with pytest.raises(ValueError, match="Invalid candidate capacity"):
        calculate_annual_wind_generation(capacity, 5.0)


def test_annual_generation_without_monthly_data_uses_the_annual_mean():
    result = calculate_annual_wind_generation(2.0, 5.0)

    expected = 2.0 * mean_power_fraction(5.0) * HOURS_PER_YEAR * LOSSES
    assert result.annual_generation_kwh == pytest.approx(expected)
    assert result.monthly_generation_kwh is None


def test_monthly_generation_uses_each_months_mean_and_real_day_count_and_sums_to_the_year():
    monthly = {m: 4.0 for m in DAYS_IN_MONTH}
    monthly["JUL"] = 7.0  # TEST FIXTURE ONLY: a windier month

    result = calculate_annual_wind_generation(1.0, 4.4, monthly)

    assert set(result.monthly_generation_kwh) == set(DAYS_IN_MONTH)
    assert sum(result.monthly_generation_kwh.values()) == pytest.approx(result.annual_generation_kwh)
    assert result.monthly_generation_kwh["JUL"] == pytest.approx(
        mean_power_fraction(7.0) * 24 * 31 * LOSSES
    )
    # Not an annual/12 split: February has 28 days, January 31.
    assert result.monthly_generation_kwh["FEB"] / result.monthly_generation_kwh["JAN"] == pytest.approx(28 / 31)


def test_with_a_constant_monthly_mean_the_monthly_path_equals_the_annual_path():
    monthly = {m: 5.0 for m in DAYS_IN_MONTH}

    with_monthly = calculate_annual_wind_generation(1.0, 5.0, monthly)
    annual_only = calculate_annual_wind_generation(1.0, 5.0)

    assert with_monthly.annual_generation_kwh == pytest.approx(annual_only.annual_generation_kwh)


def test_incomplete_monthly_data_is_ignored_not_filled_in():
    partial = {"JAN": 5.0, "FEB": 5.0}

    result = calculate_annual_wind_generation(1.0, 5.0, partial)

    assert result.monthly_generation_kwh is None


def test_capacity_factor_and_full_load_hours_are_consistent_and_net_of_losses():
    result = calculate_annual_wind_generation(3.0, 5.0)

    assert result.equivalent_full_load_hours == pytest.approx(result.annual_generation_kwh / 3.0)
    assert result.net_capacity_factor == pytest.approx(result.equivalent_full_load_hours / HOURS_PER_YEAR)
    assert result.net_capacity_factor == pytest.approx(mean_power_fraction(5.0) * LOSSES)


def test_generation_scales_linearly_with_capacity_and_never_exceeds_rated_energy():
    one = calculate_annual_wind_generation(1.0, 6.0)
    ten = calculate_annual_wind_generation(10.0, 6.0)

    assert ten.annual_generation_kwh == pytest.approx(10 * one.annual_generation_kwh)
    assert one.annual_generation_kwh <= 1.0 * HOURS_PER_YEAR
    assert one.net_capacity_factor <= LOSSES  # can never beat the loss ceiling


def test_a_very_high_mean_wind_does_not_extrapolate_output():
    result = calculate_annual_wind_generation(1.0, 40.0)  # TEST FIXTURE ONLY

    assert 0 <= result.net_capacity_factor <= LOSSES


def test_the_same_inputs_always_give_the_same_result():
    monthly = {m: 5.5 for m in DAYS_IN_MONTH}
    assert calculate_annual_wind_generation(2.0, 5.5, monthly) == calculate_annual_wind_generation(2.0, 5.5, monthly)
