import pytest

from app.engines.solar.generation import estimate_annual_generation_kwh, estimate_monthly_generation_kwh


def test_annual_generation_matches_the_documented_formula():
    # Capacity x Daily Resource x 365 x Performance Ratio
    result = estimate_annual_generation_kwh(5, 5.0, performance_ratio=0.75)
    assert result == pytest.approx(5 * 5.0 * 365 * 0.75)


def test_annual_generation_scales_linearly_with_capacity():
    one_kw = estimate_annual_generation_kwh(1, 5.0)
    five_kw = estimate_annual_generation_kwh(5, 5.0)
    assert five_kw == pytest.approx(one_kw * 5)


def test_annual_generation_rejects_invalid_capacity():
    with pytest.raises(ValueError):
        estimate_annual_generation_kwh(0, 5.0)
    with pytest.raises(ValueError):
        estimate_annual_generation_kwh(-1, 5.0)


def test_monthly_generation_uses_real_calendar_days_not_annual_over_twelve():
    monthly_resource = {"JAN": 5.0, "FEB": 6.0}
    result = estimate_monthly_generation_kwh(3, monthly_resource, performance_ratio=0.75)

    assert result["JAN"] == pytest.approx(3 * 5.0 * 31 * 0.75)
    assert result["FEB"] == pytest.approx(3 * 6.0 * 28 * 0.75)
    # Different resource values and different day-counts, so these must differ.
    assert result["JAN"] != result["FEB"]


def test_monthly_generation_rejects_invalid_capacity():
    with pytest.raises(ValueError):
        estimate_monthly_generation_kwh(0, {"JAN": 5.0})


def test_monthly_generation_ignores_unrecognized_month_keys():
    result = estimate_monthly_generation_kwh(3, {"JAN": 5.0, "NOT_A_MONTH": 9.0})
    assert set(result.keys()) == {"JAN"}
