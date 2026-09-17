import uuid
from datetime import date
from decimal import Decimal

from app.engines.incentive.incentive_engine import evaluate_incentives
from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)
from app.schemas.incentive import IncentiveProgramInput

BASE = dict(
    incentive_type=IncentiveType.CAPITAL_SUBSIDY,
    technology=RenewableTechnology.SOLAR,
    consumer_category=TariffConsumerCategory.RESIDENTIAL,
    subsidy_type=SubsidyType.FIXED_AMOUNT,
    subsidy_value=Decimal("10000"),
    verification_status=IncentiveVerificationStatus.VERIFIED,
    active=True,
)

CONTEXT = {
    "monthly_consumption_kwh": Decimal("300"),
    "roof_area_sqft": Decimal("500"),
    "land_area_sqft": None,
    "budget_inr": None,
    "backup_required": False,
}


def row(scheme_name, level, version="V1", effective_from="2026-01-01", effective_to=None, **overrides):
    data = {
        **BASE,
        "id": uuid.uuid4(),
        "scheme_name": scheme_name,
        "level": level,
        "scheme_version": version,
        "effective_from": effective_from,
        "effective_to": effective_to,
    }
    data.update(overrides)
    return IncentiveProgramInput(**data)


def run(rows, **overrides):
    kwargs = dict(
        calculation_date=date(2026, 6, 1),
        technology=RenewableTechnology.SOLAR,
        consumer_category=TariffConsumerCategory.RESIDENTIAL,
        proposed_capacity_kw=Decimal("3"),
        eligible_cost_basis_inr=None,
        available_context=CONTEXT,
    )
    kwargs.update(overrides)
    return evaluate_incentives(rows, **kwargs)


def test_single_eligible_scheme():
    results = run([row("Central Scheme", IncentiveLevel.CENTRAL)])
    assert len(results) == 1
    assert results[0].status == "eligible"


def test_expired_scheme_reported_not_silently_dropped():
    results = run([row("Old Scheme", IncentiveLevel.CENTRAL, effective_from="2020-01-01", effective_to="2021-12-31")])
    assert len(results) == 1
    assert results[0].status == "scheme_expired"
    assert results[0].eligible is False


def test_future_scheme_reported_as_not_active():
    results = run([row("Future Scheme", IncentiveLevel.CENTRAL, effective_from="2030-01-01")])
    assert results[0].status == "scheme_not_active"


def test_multiple_distinct_schemes_all_reported():
    results = run(
        [
            row("Central Scheme", IncentiveLevel.CENTRAL),
            row("State Scheme", IncentiveLevel.STATE),
        ]
    )
    assert {r.scheme_name for r in results} == {"Central Scheme", "State Scheme"}


def test_selects_latest_version_of_a_scheme_by_calculation_date():
    results = run(
        [
            row("Central Scheme", IncentiveLevel.CENTRAL, version="V1", effective_from="2024-01-01", effective_to="2025-12-31", subsidy_value=Decimal("5000")),
            row("Central Scheme", IncentiveLevel.CENTRAL, version="V2", effective_from="2026-01-01", subsidy_value=Decimal("20000")),
        ]
    )
    assert len(results) == 1
    assert results[0].incentive_amount_inr == "20000.00"


def test_two_eligible_schemes_get_flagged_for_stacking_verification():
    results = run(
        [
            row("Central Scheme", IncentiveLevel.CENTRAL),
            row("State Scheme", IncentiveLevel.STATE),
        ]
    )
    assert all(r.combination_note == "combination_requires_verification" for r in results)


def test_never_includes_subsidy_amount_for_ineligible_programme():
    results = run([row("Commercial Only Scheme", IncentiveLevel.CENTRAL, consumer_category=TariffConsumerCategory.COMMERCIAL)])
    assert results[0].eligible is False
    assert results[0].incentive_amount_inr is None


def test_no_candidate_rows_returns_empty_list():
    assert run([]) == []
