from datetime import UTC, datetime

import pytest

from app.engines.solar.sizing import estimate_roof_area_required_sqft, evaluate_candidate, evaluate_candidates
from app.schemas.location import SolarResourceProfile


def make_resource(annual=5.0, monthly=None):
    return SolarResourceProfile(
        annual_value=annual,
        monthly_values=monthly,
        unit="kWh/m^2/day",
        source="TEST",
        period_represented="TEST fixture period",
        retrieved_at=datetime.now(UTC),
    )


def test_roof_area_scales_linearly_with_capacity():
    area_1kw = estimate_roof_area_required_sqft(1)
    area_2kw = estimate_roof_area_required_sqft(2)
    assert area_2kw == pytest.approx(area_1kw * 2)


def test_roof_area_rejects_invalid_capacity():
    with pytest.raises(ValueError):
        estimate_roof_area_required_sqft(0)


def test_candidate_is_feasible_with_ample_roof_area():
    option = evaluate_candidate(3, make_resource(), roof_area_sqft=1000, annual_consumption_kwh=3000)

    assert option.technical_status == "technically_feasible"
    assert option.estimated_annual_generation_kwh > 0
    assert option.generation_coverage_percent is not None
    assert option.technical_notes == []


def test_candidate_is_infeasible_with_insufficient_roof_area():
    option = evaluate_candidate(10, make_resource(), roof_area_sqft=10, annual_consumption_kwh=3000)

    assert option.technical_status == "technically_infeasible"
    assert option.technical_notes


def test_candidate_is_insufficient_data_without_roof_area():
    option = evaluate_candidate(3, make_resource(), roof_area_sqft=None, annual_consumption_kwh=3000)

    assert option.technical_status == "insufficient_data"
    # Generation numbers don't depend on roof area, so they're still shown.
    assert option.estimated_annual_generation_kwh is not None


def test_candidates_show_the_feasible_infeasible_boundary():
    # ~73.5 sqft/kW with default assumptions -> 300 sqft fits up to 4kW.
    options = evaluate_candidates([1, 2, 3, 4, 5], make_resource(), roof_area_sqft=300, annual_consumption_kwh=3000)
    statuses = {option.capacity_kw: option.technical_status for option in options}

    assert statuses[4] == "technically_feasible"
    assert statuses[5] == "technically_infeasible"


def test_candidate_has_no_coverage_percent_for_zero_consumption():
    option = evaluate_candidate(3, make_resource(), roof_area_sqft=1000, annual_consumption_kwh=0)
    assert option.generation_coverage_percent is None


def test_candidate_includes_monthly_generation_when_available():
    option = evaluate_candidate(
        3, make_resource(monthly={"JAN": 5.0, "FEB": 6.0}), roof_area_sqft=1000, annual_consumption_kwh=3000
    )

    assert option.estimated_monthly_generation_kwh is not None
    assert "JAN" in option.estimated_monthly_generation_kwh


def test_candidate_omits_monthly_generation_when_unavailable():
    option = evaluate_candidate(3, make_resource(monthly=None), roof_area_sqft=1000, annual_consumption_kwh=3000)
    assert option.estimated_monthly_generation_kwh is None
