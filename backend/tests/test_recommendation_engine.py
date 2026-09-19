"""Recommendation Engine rules. Inputs are built with the REAL Solar Engine (so the
numbers are engine outputs, never hand-typed results); only the resource value and the
wind/tariff/incentive responses are TEST FIXTURES.
"""

from datetime import UTC, date, datetime

import pytest

from app.engines.recommendation import RecommendationInput, recommend
from app.engines.recommendation import engine as recommendation_engine
from app.engines.solar import calculate as solar_calculate
from app.models.enums import BuildingType, IncentiveLevel, RenewableTechnology, TariffConsumerCategory
from app.schemas.incentive import (
    IncentiveEligibilityResult,
    IncentiveEvaluationResponse,
    IncentiveEvaluationSummary,
    IncentiveSourceInfo,
)
from app.schemas.location import SolarResourceProfile
from app.schemas.solar import SolarEngineInput
from app.schemas.tariff import TariffCalculationResponse, TariffScheduleSummary
from app.schemas.wind import WindCalculationResponse, WindCandidate

NOW = datetime(2026, 1, 1, tzinfo=UTC)
# TEST FIXTURE: chosen so 1 kW yields 1,429.6 kWh/yr, matching the example in the brief.
EXAMPLE_RESOURCE = 5.2224


def solar_for(monthly_kwh=300, roof=600, resource=EXAMPLE_RESOURCE, building=BuildingType.HOME):
    return solar_calculate(
        SolarEngineInput(
            monthly_consumption_kwh=monthly_kwh,
            roof_area_sqft=roof,
            building_type=building,
            solar_resource=SolarResourceProfile(
                annual_value=resource, unit="kWh/m^2/day", source="TEST FIXTURE ONLY", retrieved_at=NOW
            ),
        )
    )


def wind_with(status="insufficient_resource", capacities=(0.5, 1, 2, 3, 5, 10), generation=6000.0):
    return WindCalculationResponse(
        status="ok",
        candidates=[
            WindCandidate(
                capacity_kw=c,
                annual_generation_kwh=generation * c,
                net_capacity_factor=0.2,
                equivalent_full_load_hours=1752.0,
                technical_status=status,
            )
            for c in capacities
        ],
        calculation_version="wind-engine-test",
        assumption_version="wind-assumptions-test",
        calculated_at=NOW,
    )


def wind_unavailable():
    return WindCalculationResponse(
        status="wind_resource_unavailable",
        reason="No verified wind resource is available for this location.",
        calculation_version="wind-engine-test",
        assumption_version="wind-assumptions-test",
        calculated_at=NOW,
    )


def tariff_ok():
    return TariffCalculationResponse(
        status="ok",
        tariff=TariffScheduleSummary(
            tariff_name="TEST tariff",
            tariff_version="TEST-1",
            consumer_category=TariffConsumerCategory.RESIDENTIAL,
            effective_from=date(2025, 7, 1),
        ),
        estimated_monthly_bill_inr="1234.00",
        calculation_version="tariff-test",
        calculated_at=NOW,
    )


def incentives(eligible: bool, capacity_kw: float, technology=RenewableTechnology.SOLAR, amount="78000.00"):
    return IncentiveEvaluationResponse(
        status="ok",
        technology=technology,
        proposed_capacity_kw=str(capacity_kw),
        programmes=[
            IncentiveEligibilityResult(
                scheme_name="TEST FIXTURE ONLY - Central Scheme",
                level=IncentiveLevel.CENTRAL,
                technology=technology,
                status="eligible" if eligible else "not_eligible",
                eligible=eligible,
                reason=None if eligible else "Scheme is for residential consumers only.",
                incentive_amount_inr=amount if eligible else None,
                source=IncentiveSourceInfo(source_name="TEST source", source_order_number="ORD-1", source_page="4"),
            )
        ],
        summary=IncentiveEvaluationSummary(verified_programmes=1, eligible_programmes=int(eligible), calculation_status="ok"),
        calculation_version="incentive-test",
        calculated_at=NOW,
    )


def run(
    *,
    monthly_kwh=300,
    roof=600,
    budget=None,
    backup=False,
    solar="default",
    wind="default",
    tariff="default",
    incentive_factory=None,
    resource=EXAMPLE_RESOURCE,
):
    calls = []

    def incentives_for(technology, capacity_kw):
        calls.append((technology, capacity_kw))
        return incentive_factory(technology, capacity_kw) if incentive_factory else None

    result = recommend(
        RecommendationInput(
            monthly_consumption_kwh=monthly_kwh,
            roof_area_sqft=roof,
            budget_inr=budget,
            backup_required=backup,
            solar=solar_for(monthly_kwh, roof, resource) if solar == "default" else solar,
            wind=wind_with() if wind == "default" else wind,
            tariff=tariff_ok() if tariff == "default" else tariff,
        ),
        incentives_for,
    )
    return result, calls


def decisions(result):
    return {o.capacity_kw: o.decision for o in result.solar_options_evaluated}


# ---- the example from the brief: 300 kWh/month, Chennai-like resource, 600 sq ft ----------


def test_300_kwh_home_gets_the_smallest_qualifying_solar_size():
    result, calls = run(incentive_factory=lambda t, c: incentives(True, c))

    assert result.recommendation_status == "recommended"
    assert result.recommended_technology == "solar"
    assert result.recommended_capacity_kw == 3
    assert result.technical_feasibility == "technically_feasible"
    assert result.annual_consumption_kwh == 3600
    assert result.expected_annual_generation_kwh == 4288.9
    assert result.coverage_percent == 119.1
    assert result.target_met is True
    assert result.reason_code == "smallest_capacity_meeting_target"

    by_capacity = decisions(result)
    assert by_capacity[1] == "below_target" and by_capacity[2] == "below_target"
    assert by_capacity[3] == "selected"
    assert by_capacity[4] == "larger_than_needed"
    assert calls == [("solar", 3.0)]  # incentives evaluated for exactly the recommended system


def test_the_recommendation_values_are_the_solar_engine_outputs_not_hard_coded():
    solar = solar_for()
    result, _ = run()
    option = next(o for o in solar.options if o.capacity_kw == result.recommended_capacity_kw)

    assert result.expected_annual_generation_kwh == option.estimated_annual_generation_kwh
    assert result.coverage_percent == option.generation_coverage_percent


def test_a_different_resource_gives_a_different_recommendation():
    poor, _ = run(resource=3.0)
    good, _ = run(resource=EXAMPLE_RESOURCE)

    assert poor.recommended_capacity_kw > good.recommended_capacity_kw  # 3 kW at the good resource


def test_target_is_a_single_named_constant(monkeypatch):
    monkeypatch.setattr(recommendation_engine, "TARGET_ANNUAL_COVERAGE_PERCENT", 50.0)
    result, _ = run()

    assert result.recommended_capacity_kw == 2 and result.target_coverage_percent == 50.0
    assert "50%" in result.recommendation_reason


# ---- exclusions ---------------------------------------------------------------------------


def test_insufficient_roof_excludes_oversized_capacities_and_reports_the_shortfall():
    result, _ = run(roof=100)  # room for 1 kW only (73.5 sq ft needed)

    assert result.recommended_capacity_kw == 1
    assert result.target_met is False
    assert result.reason_code == "highest_feasible_below_target"
    assert decisions(result)[2] == "excluded_infeasible" and decisions(result)[10] == "excluded_infeasible"
    assert decisions(result)[1] == "selected_best_available"
    assert any("available roof area" in limit for limit in result.limitations)


def test_no_room_for_any_size_means_no_suitable_option():
    result, _ = run(roof=40)

    assert result.recommendation_status == "no_suitable_option"
    assert result.recommended_technology is None and result.recommended_capacity_kw is None
    assert "no system is recommended" in result.recommendation_reason


def test_missing_roof_area_is_insufficient_data_not_a_guess():
    result, _ = run(roof=None)

    assert result.recommendation_status == "insufficient_data"
    assert result.reason_code == "site_data_missing"
    assert result.recommended_capacity_kw is None


def test_unavailable_solar_result_is_insufficient_data():
    result, _ = run(solar=None)

    assert result.recommendation_status == "insufficient_data"
    assert result.reason_code == "solar_result_unavailable"


def test_no_qualifying_size_picks_the_highest_feasible_and_says_so():
    result, _ = run(monthly_kwh=5000, roof=5000)  # 60,000 kWh/yr: even 10 kW falls short

    assert result.recommended_capacity_kw == 10
    assert result.target_met is False and result.coverage_percent < 100
    assert result.reason_code == "highest_feasible_below_target"
    assert any("evaluated capacities" in limit for limit in result.limitations)


# ---- wind, hybrid, battery ------------------------------------------------------------------


def test_wind_is_not_recommended_when_screening_is_insufficient():
    result, _ = run()
    wind = next(e for e in result.excluded_options if e.technology == "wind")

    assert result.recommended_technology == "solar"
    assert wind.reason_code == "insufficient_wind_resource"
    assert "insufficient" in wind.reason


def test_marginal_or_unavailable_wind_is_not_recommended():
    marginal, _ = run(wind=wind_with("marginal"))
    unavailable, _ = run(wind=wind_unavailable())

    assert next(e for e in marginal.excluded_options if e.technology == "wind").reason_code == "wind_marginal"
    unavailable_wind = next(e for e in unavailable.excluded_options if e.technology == "wind")
    assert unavailable_wind.reason_code == "wind_resource_unavailable"
    assert "No verified wind resource" in unavailable_wind.reason


def test_solar_is_preferred_when_wind_is_also_feasible():
    result, _ = run(wind=wind_with("technically_feasible"))

    assert result.recommended_technology == "solar"
    assert next(e for e in result.excluded_options if e.technology == "wind").reason_code == "solar_preferred"


def test_wind_is_recommended_only_when_no_solar_size_is_feasible_and_wind_is():
    result, calls = run(roof=40, wind=wind_with("technically_feasible"), incentive_factory=lambda t, c: incentives(False, c, RenewableTechnology.WIND))

    assert result.recommendation_status == "recommended" and result.recommended_technology == "wind"
    assert result.recommended_capacity_kw == 1  # smallest wind size whose fixture output reaches the target
    assert calls == [("wind", 1.0)]


def test_hybrid_and_battery_are_never_recommended():
    result, _ = run(backup=True)
    excluded = {e.technology: e for e in result.excluded_options}

    assert excluded["hybrid"].reason_code == "hybrid_not_evaluated"
    assert excluded["battery"].reason_code == "battery_not_sized"
    assert any("Backup power was requested" in limit for limit in result.limitations)


# ---- incentives -------------------------------------------------------------------------------


def test_residential_incentive_from_the_incentive_engine_is_listed_with_its_source():
    result, _ = run(incentive_factory=lambda t, c: incentives(True, c))

    [incentive] = result.applicable_incentives
    assert incentive.incentive_amount_inr == "78000.00"
    assert incentive.source_name == "TEST source" and incentive.source_order == "ORD-1" and incentive.source_page == "4"
    assert result.incentive_context.eligible_programmes == 1


def test_non_residential_case_does_not_get_the_residential_incentive():
    # A college: the (existing) Incentive Engine reports the residential scheme as not eligible.
    result, _ = run(
        solar=solar_for(building=BuildingType.COLLEGE), incentive_factory=lambda t, c: incentives(False, c)
    )

    assert result.applicable_incentives == []
    assert "none applies" in result.incentive_context.note
    assert any("No verified incentive currently applies" in limit for limit in result.limitations)


def test_missing_incentive_data_does_not_stop_the_recommendation():
    result, _ = run(incentive_factory=lambda t, c: None)

    assert result.recommendation_status == "recommended"
    assert result.applicable_incentives == []
    assert result.incentive_context.status == "unavailable"


# ---- tariff and cost ----------------------------------------------------------------------------


def test_missing_tariff_still_recommends_with_a_limitation():
    result, _ = run(tariff=None)
    not_configured, _ = run(
        tariff=TariffCalculationResponse(
            status="tariff_not_configured", reason="No tariff for this state.", calculation_version="t", calculated_at=NOW
        )
    )

    assert result.recommended_capacity_kw == 3 and result.tariff_context.status == "unavailable"
    assert any("No verified tariff" in limit for limit in result.limitations)
    assert not_configured.tariff_context.status == "tariff_not_configured"
    assert not_configured.tariff_context.reason == "No tariff for this state."


def test_tariff_context_carries_the_existing_tariff_result():
    result, _ = run()

    assert result.tariff_context.tariff_name == "TEST tariff"
    assert result.tariff_context.estimated_monthly_bill_inr == "1234.00"


def test_no_cost_savings_or_payback_is_ever_produced():
    without_budget, _ = run()
    with_budget, _ = run(budget=300000)

    assert without_budget.cost_context.status == "not_available"
    assert "not currently available" in without_budget.cost_context.note
    assert with_budget.cost_context.note == (
        "A budget was provided, but verified system cost data is not available, so affordability cannot yet be calculated."
    )

    def keys(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key.lower()
                yield from keys(value)
        elif isinstance(node, list):
            for item in node:
                yield from keys(item)

    found = set(keys(with_budget.model_dump(mode="json")))
    for forbidden in ("savings", "payback", "roi", "installation_cost", "system_cost_inr", "price"):
        assert forbidden not in found


# ---- determinism and isolation ------------------------------------------------------------------


def test_identical_inputs_give_identical_recommendations():
    first, _ = run(incentive_factory=lambda t, c: incentives(True, c))
    second, _ = run(incentive_factory=lambda t, c: incentives(True, c))

    assert first.model_dump(exclude={"calculated_at"}) == second.model_dump(exclude={"calculated_at"})


def test_recommendations_for_different_assessments_do_not_leak_into_each_other():
    small, _ = run(monthly_kwh=300)
    large, _ = run(monthly_kwh=900, roof=1500)
    small_again, _ = run(monthly_kwh=300)

    assert small.recommended_capacity_kw == 3 and large.recommended_capacity_kw == 8
    assert small.annual_consumption_kwh == 3600 and large.annual_consumption_kwh == 10800
    assert small.model_dump(exclude={"calculated_at"}) == small_again.model_dump(exclude={"calculated_at"})


@pytest.mark.parametrize("field", ["rules", "recommendation_version", "engine_versions"])
def test_result_is_auditable(field):
    result, _ = run()

    assert getattr(result, field)
