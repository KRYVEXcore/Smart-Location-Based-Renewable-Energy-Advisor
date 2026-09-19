"""Wind Engine behavior. Every resource below is a TEST FIXTURE ONLY value;
none of it is real wind data and none of it may reach production.
"""

from datetime import UTC, datetime

import pytest

from app.engines.wind import calculate
from app.engines.wind.assumptions import ASSUMPTION_VERSION, CANDIDATE_CAPACITIES_KW, DAYS_IN_MONTH
from app.schemas.location import WindResourceProfile, WindSpeedReading
from app.schemas.wind import WindEngineInput


def resource(annual=5.0, monthly=None, unit="m/s", height=10.0, extra=None) -> WindResourceProfile:
    """TEST FIXTURE ONLY."""
    readings = [WindSpeedReading(reference_height_m=height, annual_value=annual, monthly_values=monthly, unit=unit)]
    readings += extra or []
    return WindResourceProfile(
        readings=readings,
        source="TEST FIXTURE ONLY",
        period_represented="test period",
        retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def run(res, **kwargs):
    return calculate(WindEngineInput(wind_resource=res, **kwargs))


def test_a_valid_resource_gives_one_result_per_configured_candidate():
    result = run(resource())

    assert result.status == "ok"
    assert [c.capacity_kw for c in result.candidates] == CANDIDATE_CAPACITIES_KW == [0.5, 1, 2, 3, 5, 10]
    assert result.assumption_version == ASSUMPTION_VERSION
    assert result.methodology and result.turbine_model and result.assumptions and result.limitations


def test_candidate_capacities_are_configurable():
    result = calculate(WindEngineInput(wind_resource=resource()), capacities_kw=[1.5, 4])

    assert [c.capacity_kw for c in result.candidates] == [1.5, 4]


@pytest.mark.parametrize("bad", [0, -2, [1, 0], [1, -1]])
def test_an_invalid_configured_capacity_is_rejected(bad):
    capacities = bad if isinstance(bad, list) else [bad]
    with pytest.raises(ValueError, match="Invalid candidate capacity"):
        calculate(WindEngineInput(wind_resource=resource()), capacities_kw=capacities)


def test_a_missing_resource_is_wind_resource_unavailable_never_a_default():
    result = run(None)

    assert result.status == "wind_resource_unavailable"
    assert result.candidates == [] and result.resource is None
    assert "No verified wind resource" in result.reason


@pytest.mark.parametrize(
    "res, fragment",
    [
        (resource(height=50.0), "10 m reference height"),  # only the 50 m reading: never reused as 10 m
        (resource(unit="km/h"), "Unsupported wind unit"),
        (resource(unit="knots"), "Unsupported wind unit"),
        (resource(annual=None), "no usable annual value"),
        (resource(annual=0.0), "non-positive"),
        (resource(annual=-3.0), "non-positive"),
        (resource(monthly={"JAN": 0.0}), "non-positive monthly"),
    ],
)
def test_an_unusable_resource_is_insufficient_data_with_a_reason(res, fragment):
    result = run(res)

    assert result.status == "insufficient_data"
    assert fragment in result.reason
    assert result.candidates == []


def test_the_10m_reading_is_used_and_the_50m_reading_is_shown_but_not_used():
    fifty = WindSpeedReading(reference_height_m=50.0, annual_value=9.9, unit="m/s")  # TEST FIXTURE ONLY

    result = run(resource(annual=4.0, extra=[fifty]))

    assert result.resource.used_reference_height_m == 10.0
    assert result.resource.used_annual_mean_speed_mps == 4.0
    assert [r.reference_height_m for r in result.resource.readings] == [10.0, 50.0]
    only_ten = run(resource(annual=4.0))
    assert [c.annual_generation_kwh for c in result.candidates] == [c.annual_generation_kwh for c in only_ten.candidates]


def test_resource_provenance_is_passed_through_and_labelled_as_a_model_value():
    result = run(resource())

    assert result.resource.provider == "TEST FIXTURE ONLY"
    assert result.resource.period_represented == "test period"
    assert result.resource.retrieved_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert "Not a live or on-site measurement" in result.resource.data_type


def test_monthly_generation_is_returned_only_when_all_twelve_months_exist():
    monthly = {m: 5.0 for m in DAYS_IN_MONTH}

    with_monthly = run(resource(monthly=monthly))
    without = run(resource())

    assert with_monthly.resource.used_monthly_means is True
    assert all(c.monthly_generation_kwh and len(c.monthly_generation_kwh) == 12 for c in with_monthly.candidates)
    assert without.resource.used_monthly_means is False
    assert all(c.monthly_generation_kwh is None for c in without.candidates)


@pytest.mark.parametrize(
    "mean_speed, expected",
    [
        (2.0, "insufficient_resource"),
        (4.0, "insufficient_resource"),  # net capacity factor ~7% < 8%
        (5.0, "marginal"),  # ~14%
        (6.5, "technically_feasible"),
        (9.0, "technically_feasible"),
    ],
)
def test_technical_status_follows_the_documented_screening_thresholds(mean_speed, expected):
    result = run(resource(annual=mean_speed))

    assert {c.technical_status for c in result.candidates} == {expected}
    assert "threshold" in result.candidates[0].technical_notes[0]


def test_results_have_generation_capacity_factor_and_full_load_hours():
    result = run(resource(annual=6.0))

    for candidate in result.candidates:
        assert candidate.annual_generation_kwh > 0
        assert 0 < candidate.net_capacity_factor < 1
        assert candidate.equivalent_full_load_hours == pytest.approx(
            candidate.annual_generation_kwh / candidate.capacity_kw, rel=1e-3
        )
        assert candidate.annual_generation_kwh <= candidate.capacity_kw * 8760


def test_generation_is_proportional_to_capacity():
    by_capacity = {c.capacity_kw: c.annual_generation_kwh for c in run(resource(annual=6.0)).candidates}

    assert by_capacity[10] == pytest.approx(20 * by_capacity[0.5], rel=1e-3)


def test_the_same_input_always_gives_the_same_numbers():
    first = run(resource(annual=5.3, monthly={m: 5.3 for m in DAYS_IN_MONTH}))
    second = run(resource(annual=5.3, monthly={m: 5.3 for m in DAYS_IN_MONTH}))

    assert [c.model_dump() for c in first.candidates] == [c.model_dump() for c in second.candidates]


@pytest.mark.parametrize(
    "roof, land, expected",
    [
        (None, None, "cannot yet be fully evaluated"),
        (1200.0, None, "roof 1,200 sq ft"),
        (None, 5000.0, "land 5,000 sq ft"),
        (800.0, 2000.0, "roof 800 sq ft, land 2,000 sq ft"),
    ],
)
def test_site_space_is_reported_but_never_used_to_claim_suitability(roof, land, expected):
    note = run(resource(), roof_area_sqft=roof, land_area_sqft=land).site_space_note

    assert expected in note
    assert "safe" not in note.lower() and "suitable" not in note.lower().replace("structural suitability", "")


def test_the_response_never_recommends_or_prices_anything():
    dump = run(resource(annual=8.0)).model_dump_json().lower()

    for forbidden in ("recommend", "subsid", "payback", "savings", "roi", "cost", "best"):
        assert forbidden not in dump.replace("not a recommendation", "").replace("no cost, subsidy, savings or payback", "")


def test_the_required_limitations_are_stated():
    text = " ".join(run(resource()).limitations)

    for phrase in ("Technical screening only", "not an anemometer", "Urban turbulence", "hub height", "not a recommendation"):
        assert phrase.lower() in text.lower()
