from datetime import UTC, datetime

from app.engines.solar.assumptions import ASSUMPTION_VERSION, ENGINE_CALCULATION_VERSION
from app.engines.solar.solar_engine import calculate
from app.models.enums import BuildingType
from app.schemas.location import SolarResourceProfile
from app.schemas.solar import SolarEngineInput


def make_resource(**overrides):
    defaults = dict(
        annual_value=5.0,
        monthly_values={"JAN": 4.5, "FEB": 5.5},
        unit="kWh/m^2/day",
        source="TEST",
        period_represented="TEST fixture 2001-2020 climatology",
        retrieved_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return SolarResourceProfile(**defaults)


def test_calculate_returns_ok_with_all_candidate_capacities():
    engine_input = SolarEngineInput(
        monthly_consumption_kwh=300,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=make_resource(),
    )

    result = calculate(engine_input)

    assert result.status == "ok"
    assert len(result.options) == 10
    assert result.annual_consumption_kwh == 3600
    assert result.calculation_version == ENGINE_CALCULATION_VERSION
    assert result.assumption_version == ASSUMPTION_VERSION
    assert result.reason is None


def test_calculate_reports_insufficient_data_without_solar_resource():
    engine_input = SolarEngineInput(
        monthly_consumption_kwh=300,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=None,
    )

    result = calculate(engine_input)

    assert result.status == "insufficient_data"
    assert result.reason is not None
    assert result.options == []


def test_calculate_reports_insufficient_data_for_zero_consumption():
    engine_input = SolarEngineInput(
        monthly_consumption_kwh=0,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=make_resource(),
    )

    assert calculate(engine_input).status == "insufficient_data"


def test_calculate_reports_insufficient_data_for_negative_consumption():
    engine_input = SolarEngineInput(
        monthly_consumption_kwh=-100,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=make_resource(),
    )

    assert calculate(engine_input).status == "insufficient_data"


def test_calculate_reports_insufficient_data_for_unsupported_resource_unit():
    engine_input = SolarEngineInput(
        monthly_consumption_kwh=300,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=make_resource(unit="W/m^2"),
    )

    result = calculate(engine_input)
    assert result.status == "insufficient_data"
    assert "unit" in result.reason.lower()


def test_calculate_is_reproducible_for_identical_input():
    engine_input = SolarEngineInput(
        monthly_consumption_kwh=450,
        roof_area_sqft=800,
        building_type=BuildingType.OFFICE,
        solar_resource=make_resource(),
    )

    first = calculate(engine_input)
    second = calculate(engine_input)

    assert first.options == second.options
    assert first.annual_consumption_kwh == second.annual_consumption_kwh
    assert first.calculation_version == second.calculation_version
    assert first.assumption_version == second.assumption_version


def test_calculate_produces_different_results_for_different_solar_resource():
    low = SolarEngineInput(
        monthly_consumption_kwh=300,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=make_resource(annual_value=3.0),
    )
    high = SolarEngineInput(
        monthly_consumption_kwh=300,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=make_resource(annual_value=6.0),
    )

    low_result = calculate(low)
    high_result = calculate(high)

    assert high_result.options[0].estimated_annual_generation_kwh > low_result.options[0].estimated_annual_generation_kwh


def test_calculate_never_labels_a_result_as_recommended_or_optimal():
    engine_input = SolarEngineInput(
        monthly_consumption_kwh=300,
        roof_area_sqft=1000,
        building_type=BuildingType.HOME,
        solar_resource=make_resource(),
    )

    result = calculate(engine_input)

    for option in result.options:
        assert option.technical_status in {
            "technically_feasible",
            "technically_infeasible",
            "insufficient_data",
        }
