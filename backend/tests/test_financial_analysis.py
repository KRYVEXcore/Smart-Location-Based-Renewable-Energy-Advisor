"""Financial Analysis Engine (Phase 11). The pure engine is tested with hand-built inputs; the API
tests use the REAL Solar and Tariff engines over the fake location providers, so every expected
number is derived from another engine's output, never typed in. No AI provider is ever called.
"""

import copy
import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.engines.financial import FinancialInput, analyse, cost_context_for
from app.engines.financial.costs import gross_cost, load_cost_records
from app.engines.financial.engine import _net, _payback
from app.main import app
from app.schemas.recommendation import (
    CostContext,
    InrRange,
    RecommendationResult,
    RecommendedIncentive,
)
from app.services.ai.prompt import SYSTEM_PROMPT
from app.services.ai.rate_limit import chat_rate_limiter
from app.schemas.location import SolarResourceProfile
from tests.location_fakes import FakeSolarProvider
from tests.test_advisor import FakeChatProvider, _chat, _context, _seed_incentive
from tests.test_advisor import _setup as _setup_locations
from tests.test_recommendation_api import Tripwire, _create, _recommendation
from tests.test_tariff_api import _seed_tariff

RECORDS = load_cost_records()
# TEST FIXTURE: a full 12-month resource (the shared fake provider only returns one month). A real
# provider returns twelve months; the engine refuses to model savings from fewer.
TWELVE_MONTH_RESOURCE = SolarResourceProfile(
    annual_value=5.2224,
    monthly_values=dict(zip(
        ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
        [4.5, 5.5, 6.2, 6.5, 6.4, 5.4, 5.0, 5.0, 5.2, 4.6, 4.0, 4.0],
        strict=True,
    )),
    unit="kWh/m^2/day",
    source="TEST FIXTURE ONLY",
    retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
)


def _setup(db_session, provider, **kwargs):
    _setup_locations(db_session, provider, solar_provider=FakeSolarProvider(result=TWELVE_MONTH_RESOURCE), **kwargs)

MONTHLY_KWH = 800.0
TWELVE = {str(month): 800.0 for month in range(1, 13)}


@pytest.fixture(autouse=True)
def _reset():
    chat_rate_limiter.clear()
    yield
    chat_rate_limiter.clear()
    app.dependency_overrides.clear()


def _recommendation_for(kw=7.0, *, technology="solar", status="recommended", incentive="78000.00"):
    incentives = [RecommendedIncentive(scheme_name="PM Surya Ghar", level="central", incentive_amount_inr=incentive)] if incentive else []
    return RecommendationResult(
        recommendation_status=status,
        recommended_technology=technology if status == "recommended" else None,
        recommended_capacity_kw=kw if status == "recommended" else None,
        target_coverage_percent=100.0,
        reason_code="x",
        recommendation_reason="reason",
        applicable_incentives=incentives,
        cost_context=CostContext(note="n"),
        recommendation_version="t",
        calculated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _linear(rate):
    return lambda kwh: Decimal(str(rate)) * kwh  # TEST FIXTURE tariff: a flat rate, no fixed charge


def _run(rec=None, *, state="Tamil Nadu", category="residential", generation=None, bill_at=_linear(5), consumption=MONTHLY_KWH):
    return analyse(
        FinancialInput(
            recommendation=rec or _recommendation_for(),
            state=state,
            consumer_category=category,
            monthly_consumption_kwh=consumption,
            monthly_generation_kwh=TWELVE if generation is None else generation,
            bill_at=bill_at,
            tariff_name="TEST tariff",
            tariff_version="TEST-1",
            cost_records=RECORDS,
        )
    )


def _without_time(result):
    return result.model_dump(mode="json", exclude={"calculated_at"})


# ---- cost dataset -----------------------------------------------------------------------------------


def test_every_cost_record_names_its_source_and_the_dataset_is_verified():
    assert RECORDS
    for record in RECORDS:
        assert record.verification_status == "verified"
        assert record.source_url.startswith("https://") and record.source_document and record.source_page
        assert record.source_excerpt and record.effective_from and record.last_verified
        assert record.gst_treatment and record.inclusions and record.exclusions and record.capacity_basis


def test_gross_cost_uses_the_exact_recommended_capacity():
    def cost(kw):
        return gross_cost(RECORDS, kw, "Tamil Nadu", "residential")[0]

    assert cost(7).low == cost(7).high == 2 * 50000 + 5 * 45000  # never a 3 kW figure
    assert cost(3).low == 2 * 50000 + 45000
    assert cost(1).low == 50000
    assert len({cost(1).low, cost(3).low, cost(7).low}) == 3


def test_special_category_states_use_their_own_benchmark():
    assert gross_cost(RECORDS, 7, "Assam", "residential")[0].low == 2 * 55000 + 5 * 49500
    assert gross_cost(RECORDS, 7, "Jammu and Kashmir", "residential")[0].low == 2 * 55000 + 5 * 49500
    assert gross_cost(RECORDS, 7, "Tamil Nadu", "residential")[0].low == 325000


def test_no_verified_record_means_no_cost_never_a_guess():
    assert gross_cost(RECORDS, 7, "Tamil Nadu", "educational_institution") is None  # residential benchmark only
    assert gross_cost(RECORDS, 7, "Tamil Nadu", "commercial") is None
    assert gross_cost(RECORDS, 7, None, "residential") is None
    assert gross_cost([], 7, "Tamil Nadu", "residential") is None


def test_the_cost_basis_carries_its_provenance():
    basis = _run().cost_basis

    assert basis.cost_kind == "benchmark" and basis.source_name.startswith("Ministry of New and Renewable Energy")
    assert basis.source_url.startswith("https://") and basis.source_page == "8"
    assert basis.gst_treatment and basis.inclusions and basis.exclusions and basis.last_verified


# ---- engine: cost, incentive, net -------------------------------------------------------------------


def test_the_chennai_style_case_is_complete_with_the_verified_incentive_applied():
    result = _run()

    assert result.status == "complete"
    assert result.capacity_kw == 7
    assert result.gross_cost_range_inr == InrRange(low=325000, high=325000)
    assert result.incentive_inr == 78000 and result.incentive_scheme == "PM Surya Ghar"
    assert result.net_investment_range_inr == InrRange(low=247000, high=247000)


def test_a_college_is_never_given_a_residential_cost_or_incentive():
    result = _run(_recommendation_for(incentive=None), category="educational_institution")

    assert result.cost_status == "not_available" and result.gross_cost_range_inr is None
    assert result.incentive_inr is None and result.net_investment_range_inr is None
    assert result.status == "cost_unavailable"  # savings are still modelled; nothing else is invented
    assert result.simple_payback_years_range is None and "net investment is not available" in result.payback_note


def test_missing_cost_data_is_unavailable_not_zero():
    result = _run(state=None)

    assert result.status == "cost_unavailable"
    assert result.gross_cost_range_inr is None and result.net_investment_range_inr is None
    assert result.annual_savings_inr and result.annual_savings_inr > 0  # the engine still works without cost data
    assert "cost" in result.reason.lower()


def test_net_investment_is_never_negative_and_ranges_are_preserved():
    assert _net(InrRange(low=100, high=300), 500) == InrRange(low=0, high=0)
    net = _net(InrRange(low=100000, high=140000), 30000)
    assert net == InrRange(low=70000, high=110000)  # both ends kept: no midpoint

    payback = _payback(net, 35000)[0]
    assert (payback.low, payback.high) == (2.0, 3.1)


def test_several_eligible_incentives_are_not_assumed_to_stack():
    rec = _recommendation_for()
    rec.applicable_incentives.append(RecommendedIncentive(scheme_name="State top-up", level="state", incentive_amount_inr="10000.00"))

    result = _run(rec)

    assert result.incentive_inr == 78000 and "not verified" in result.incentive_note  # largest only, not 88,000
    assert result.net_investment_range_inr.low == 247000


# ---- engine: savings and payback --------------------------------------------------------------------


def test_savings_come_from_the_tariff_engine_not_from_bill_divided_by_units():
    result = _run(generation={str(m): 400.0 for m in range(1, 13)}, bill_at=_linear(5))

    # half of 800 kWh a month is replaced: 400 kWh x the tariff's 5 = 2,000 a month
    assert result.monthly_savings_inr == 2000 and result.annual_savings_inr == 24000
    assert result.baseline_annual_bill_inr == 48000 and result.annual_bill_after_solar_inr == 24000
    assert result.tariff_name == "TEST tariff" and result.savings_status == "available"


def test_a_fixed_charge_is_not_counted_as_a_saving():
    result = _run(bill_at=lambda kwh: Decimal("100") + Decimal("5") * kwh)  # TEST FIXTURE: 100 fixed + 5 a unit

    assert result.annual_savings_inr == 12 * 5 * 800  # only the energy part; the fixed charge stays


def test_surplus_generation_is_not_valued_and_coverage_above_100_is_not_extra_savings():
    result = _run(generation={str(m): 1600.0 for m in range(1, 13)})  # 200% coverage

    assert result.annual_savings_inr == 12 * 5 * 800  # capped at what the customer uses, not 1,600
    assert result.annual_bill_after_solar_inr == 0
    assert result.annual_surplus_generation_kwh == 12 * 800
    assert any("Export or net-metering compensation is not modelled" in item for item in result.limitations)


def test_seasonal_generation_is_offset_month_by_month():
    generation = {str(m): (1200.0 if m <= 6 else 200.0) for m in range(1, 13)}

    result = _run(generation=generation)

    assert result.annual_self_consumed_kwh == 6 * 800 + 6 * 200
    assert result.annual_surplus_generation_kwh == 6 * 400
    assert result.annual_savings_inr == 5 * (6 * 800 + 6 * 200)


def test_missing_tariff_makes_savings_unavailable_and_never_zero():
    result = _run(bill_at=None)

    assert result.status == "savings_unavailable"
    assert result.annual_savings_inr is None and result.monthly_savings_inr is None
    assert result.simple_payback_years_range is None and "savings cannot be modelled" in result.payback_note
    assert result.gross_cost_range_inr is not None  # the cost is still shown


@pytest.mark.parametrize(
    "overrides",
    [{"generation": {"1": 800.0}}, {"consumption": None}, {"consumption": 0}, {"bill_at": lambda kwh: None}],
)
def test_unsafe_savings_inputs_are_unavailable(overrides):
    result = _run(**overrides)

    assert result.savings_status == "not_available" and result.annual_savings_inr is None
    assert result.simple_payback_years_range is None


def test_zero_savings_never_produce_a_payback():
    result = _run(bill_at=lambda kwh: Decimal("500"))  # TEST FIXTURE: a bill that does not depend on units

    assert result.annual_savings_inr == 0
    assert result.simple_payback_years_range is None and "not above zero" in result.payback_note


def test_payback_is_net_investment_over_annual_savings_only():
    result = _run(generation={str(m): 400.0 for m in range(1, 13)})

    assert result.simple_payback_years_range.low == result.simple_payback_years_range.high == round(247000 / 24000, 1)
    assert result.payback_note == "Estimated simple payback = net investment / estimated annual savings."
    assert any("tariff escalation" in item and "financing" in item for item in result.limitations)


def test_no_recommendation_means_nothing_to_analyse():
    assert _run(_recommendation_for(status="no_suitable_option")).status == "not_applicable"
    assert _run(_recommendation_for(status="insufficient_data")).status == "insufficient_data"
    for status in ("no_suitable_option", "insufficient_data"):
        result = _run(_recommendation_for(status=status))
        assert result.gross_cost_range_inr is None and result.annual_savings_inr is None


def test_wind_has_no_verified_cost_or_savings_model():
    result = _run(_recommendation_for(2.0, technology="wind", incentive=None))

    assert result.status == "insufficient_data" and result.gross_cost_range_inr is None and result.annual_savings_inr is None


def test_the_analysis_is_deterministic():
    assert _without_time(_run()) == _without_time(_run())


def test_capacities_above_the_subsidy_cap_are_flagged():
    assert any("up to 3 kW" in item for item in _run().limitations)
    assert not any("up to 3 kW" in item for item in _run(_recommendation_for(3.0)).limitations)


# ---- recommendation cost_context --------------------------------------------------------------------

STATE_A = "Technical recommendation. A budget was provided, but verified system cost data is not available, so affordability cannot yet be calculated."


def test_cost_context_states_a_b_and_c():
    with_cost = cost_context_for(_run(), 300000)
    no_cost_budget = cost_context_for(_run(state=None), 300000)
    no_cost_no_budget = cost_context_for(_run(state=None), None)

    assert with_cost.status == "available" and with_cost.installed_cost_range_inr.low == 325000
    assert with_cost.incentive_inr == 78000 and with_cost.net_investment_range_inr.low == 247000
    assert with_cost.annual_savings_inr and with_cost.monthly_savings_inr and with_cost.simple_payback_years_range
    assert "affordability cannot yet be calculated" not in with_cost.note

    assert no_cost_budget.status == "not_available"
    assert no_cost_budget.note == "A budget was provided, but verified system cost data is not available, so affordability cannot yet be calculated."
    assert no_cost_no_budget.note == "Verified system cost data is not currently available."
    assert no_cost_budget.installed_cost_range_inr is None and no_cost_budget.simple_payback_years_range is None


# ---- API (real Solar and Tariff engines) ------------------------------------------------------------


def _financial(client, aid):
    return client.get(f"/api/v1/financial-analysis/{aid}")


def _monthly_generation(client, aid, capacity):
    options = client.post("/api/v1/solar/calculate", json={"assessment_id": aid}).json()["options"]
    return next(o for o in options if o["capacity_kw"] == capacity)["estimated_monthly_generation_kwh"]


def test_the_endpoint_returns_the_analysis_and_never_calls_an_ai(client, valid_payload, db_session):
    _setup(db_session, Tripwire())
    _seed_tariff(db_session, state="Tamil Nadu", energy_charge_inr_per_kwh=5.0)
    _seed_incentive(db_session)
    aid = _create(client, valid_payload)

    response = _financial(client, aid)

    assert response.status_code == 200
    body = response.json()
    rec = _recommendation(client, aid).json()
    kw = rec["recommended_capacity_kw"]
    expected_gross = 2 * 50000 + (kw - 2) * 45000 if kw > 2 else kw * 50000
    assert body["assessment_id"] == aid and body["status"] == "complete" and body["capacity_kw"] == kw
    assert body["gross_cost_range_inr"] == {"low": expected_gross, "high": expected_gross}
    assert body["incentive_inr"] == 15000  # TEST FIXTURE incentive from the existing Incentive Engine
    assert body["net_investment_range_inr"]["low"] == expected_gross - 15000
    assert body["cost_basis"]["source_url"].startswith("https://") and body["calculation_version"]
    assert body["methodology"] and body["limitations"]


def test_savings_equal_the_tariff_engine_applied_to_the_monthly_solar_offset(client, valid_payload, db_session):
    _setup(db_session, FakeChatProvider())
    _seed_tariff(db_session, state="Tamil Nadu", energy_charge_inr_per_kwh=5.0)
    aid = _create(client, valid_payload, monthly=300)

    body = _financial(client, aid).json()
    generation = _monthly_generation(client, aid, body["capacity_kw"])

    expected = round(sum(5.0 * min(value, 300) for value in generation.values()), 2)
    assert body["annual_savings_inr"] == expected
    assert body["monthly_savings_inr"] == round(expected / 12, 2)
    assert body["baseline_annual_bill_inr"] == 12 * 5.0 * 300
    assert body["tariff_name"] == "TEST Domestic Tariff"
    assert body["simple_payback_years_range"]["low"] == round(body["net_investment_range_inr"]["low"] / expected, 1)


def test_without_a_tariff_the_endpoint_says_savings_are_unavailable(client, valid_payload, db_session):
    _setup(db_session, FakeChatProvider())
    aid = _create(client, valid_payload)

    body = _financial(client, aid).json()

    assert body["status"] == "savings_unavailable" and body["cost_status"] == "available"
    assert body["annual_savings_inr"] is None and body["monthly_savings_inr"] is None
    assert body["simple_payback_years_range"] is None


def test_a_college_gets_neither_the_residential_cost_nor_incentive(client, valid_payload, db_session):
    _setup(db_session, FakeChatProvider())
    _seed_incentive(db_session)  # residential-only scheme
    aid = _create(client, valid_payload, building="college")

    body = _financial(client, aid).json()

    assert body["status"] == "insufficient_data" and body["cost_status"] == "not_available"
    assert body["incentive_inr"] is None and body["gross_cost_range_inr"] is None and body["net_investment_range_inr"] is None


def test_unknown_assessment_is_404_and_nothing_recommended_is_not_applicable(client, valid_payload, db_session):
    import uuid

    _setup(db_session, FakeChatProvider())
    assert _financial(client, str(uuid.uuid4())).status_code == 404

    body = _financial(client, _create(client, valid_payload, roof=None)).json()
    assert body["status"] == "insufficient_data" and body["gross_cost_range_inr"] is None and body["annual_savings_inr"] is None


def test_two_assessments_never_share_a_financial_result(client, valid_payload, db_session):
    _setup(db_session, FakeChatProvider())
    _seed_tariff(db_session, state="Tamil Nadu", energy_charge_inr_per_kwh=5.0)
    small = _create(client, valid_payload, monthly=300, roof=600)
    large = _create(client, valid_payload, monthly=900, roof=1500)

    first, second = _financial(client, small).json(), _financial(client, large).json()

    assert first["capacity_kw"] < second["capacity_kw"]
    assert first["gross_cost_range_inr"]["low"] < second["gross_cost_range_inr"]["low"]
    assert first["baseline_annual_bill_inr"] == 12 * 5 * 300 and second["baseline_annual_bill_inr"] == 12 * 5 * 900
    assert _financial(client, small).json()["annual_savings_inr"] == first["annual_savings_inr"]


def test_the_recommendation_cost_context_carries_the_same_analysis(client, valid_payload, db_session):
    _setup(db_session, FakeChatProvider())
    _seed_tariff(db_session, state="Tamil Nadu", energy_charge_inr_per_kwh=5.0)
    _seed_incentive(db_session)
    aid = _create(client, valid_payload, budget=300000)

    cost = _recommendation(client, aid).json()["cost_context"]
    financial = _financial(client, aid).json()

    assert cost["status"] == "available"
    assert cost["installed_cost_range_inr"] == financial["gross_cost_range_inr"]
    assert cost["incentive_inr"] == financial["incentive_inr"]
    assert cost["net_investment_range_inr"] == financial["net_investment_range_inr"]
    assert cost["annual_savings_inr"] == financial["annual_savings_inr"]
    assert cost["monthly_savings_inr"] == financial["monthly_savings_inr"]
    assert cost["simple_payback_years_range"] == financial["simple_payback_years_range"]
    assert cost["budget_inr"] == 300000


def test_the_recommendation_keeps_the_two_cost_unavailable_messages(client, valid_payload, db_session):
    _setup(db_session, FakeChatProvider())
    with_budget = _create(client, valid_payload, budget=300000, building="college")
    without_budget = _create(client, valid_payload, building="college")

    a = _recommendation(client, with_budget).json()
    c = _recommendation(client, without_budget).json()

    assert a["recommendation_status"] == "recommended" and a["cost_context"]["status"] == "not_available"
    assert a["cost_context"]["note"] == STATE_A.removeprefix("Technical recommendation. ")
    assert c["cost_context"]["note"] == "Verified system cost data is not currently available."
    assert a["cost_context"]["note"] in a["limitations"]  # the limitation follows the same wording


# ---- SHREA AI ---------------------------------------------------------------------------------------


def test_the_advisor_context_carries_the_financial_analysis_exactly(client, valid_payload, db_session):
    provider = FakeChatProvider()
    _setup(db_session, provider)
    _seed_tariff(db_session, state="Tamil Nadu", energy_charge_inr_per_kwh=5.0)
    _seed_incentive(db_session)
    aid = _create(client, valid_payload)
    api = _financial(client, aid).json()

    _chat(client, aid, "What will my system cost?")
    section = _context(provider)["financial_analysis"]

    assert section["status"] == "complete" and section["capacity_kw"] == api["capacity_kw"]
    assert section["gross_cost_range_inr"] == api["gross_cost_range_inr"]
    assert section["net_investment_range_inr"] == api["net_investment_range_inr"]
    assert section["incentive_inr"] == api["incentive_inr"]
    assert section["estimated_annual_savings_inr"] == api["annual_savings_inr"]
    assert section["estimated_monthly_savings_inr"] == api["monthly_savings_inr"]
    assert section["estimated_simple_payback_years_range"] == api["simple_payback_years_range"]
    assert section["cost_basis"]["source"].startswith("Ministry of New and Renewable Energy")
    assert "not_calculated" not in json.dumps(section)


def test_the_advisor_context_reports_missing_financial_values_as_absent(client, valid_payload, db_session):
    provider = FakeChatProvider()
    _setup(db_session, provider)
    aid = _create(client, valid_payload, building="college")  # no verified cost for a college

    _chat(client, aid, "What will I save?")
    section = _context(provider)["financial_analysis"]

    assert section["status"] == "insufficient_data" and section["reason"]
    for absent in ("gross_cost_range_inr", "net_investment_range_inr", "estimated_annual_savings_inr", "estimated_simple_payback_years_range"):
        assert absent not in section


def test_the_prompt_makes_the_model_quote_the_financial_result_and_never_recompute(client, valid_payload, db_session):
    for rule in (
        "Use its values exactly",
        "Never compute a different cost, incentive, net investment, savings or payback yourself",
        "Call every figure \"estimated\"",
        "never turn it into a single figure",
        "Never fill it in",
        "Coverage above 100% does not mean savings above 100%",
        "Never promise savings, payback, future tariffs or investment returns",
        "What will my system cost?",
        "What is my payback?",
        "Explain my financial report",
    ):
        assert rule in SYSTEM_PROMPT
    assert "It has no cost, savings, payback or ROI result" not in SYSTEM_PROMPT


def test_the_overview_suggests_the_financial_questions_without_any_ai_call(client, valid_payload, db_session):
    _setup(db_session, Tripwire())
    _seed_tariff(db_session, state="Tamil Nadu", energy_charge_inr_per_kwh=5.0)
    aid = _create(client, valid_payload)

    body = client.get(f"/api/v1/advisor/overview/{aid}").json()

    assert body["available"]["financial_analysis"] is True
    assert {"What will my system cost?", "What will I save?", "What is my payback?"} <= set(body["suggested_questions"])


def test_no_financial_field_is_ever_an_invented_number(client, valid_payload, db_session):
    _setup(db_session, FakeChatProvider())
    aid = _create(client, valid_payload, building="college")

    body = _financial(client, aid).json()
    numeric = {k: v for k, v in body.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}

    assert numeric == {"capacity_kw": body["capacity_kw"]}  # everything else is null, not 0
    assert copy.deepcopy(body["gross_cost_range_inr"]) is None
