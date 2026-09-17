import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.engines.incentive.eligibility import evaluate_program_eligibility
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
    id=uuid.uuid4(),
    scheme_name="TEST FIXTURE ONLY — Residential Solar Scheme",
    scheme_version="TEST-V1",
    level=IncentiveLevel.CENTRAL,
    incentive_type=IncentiveType.CAPITAL_SUBSIDY,
    technology=RenewableTechnology.SOLAR,
    consumer_category=TariffConsumerCategory.RESIDENTIAL,
    subsidy_type=SubsidyType.FIXED_AMOUNT,
    subsidy_value=Decimal("15000"),
    effective_from=date(2026, 1, 1),
    verification_status=IncentiveVerificationStatus.VERIFIED,
    active=True,
)

DEFAULT_CONTEXT = {
    "monthly_consumption_kwh": Decimal("300"),
    "roof_area_sqft": Decimal("500"),
    "land_area_sqft": None,
    "budget_inr": None,
    "backup_required": False,
}


def program(**overrides) -> IncentiveProgramInput:
    data = {**BASE}
    data.update(overrides)
    return IncentiveProgramInput(**data)


def evaluate(prog, **overrides):
    kwargs = dict(
        technology=RenewableTechnology.SOLAR,
        consumer_category=TariffConsumerCategory.RESIDENTIAL,
        proposed_capacity_kw=Decimal("3"),
        eligible_cost_basis_inr=None,
        available_context=DEFAULT_CONTEXT,
    )
    kwargs.update(overrides)
    return evaluate_program_eligibility(prog, **kwargs)


def test_verified_matching_scheme_is_eligible():
    result = evaluate(program())
    assert result.status == "eligible"
    assert result.eligible is True
    assert result.incentive_amount_inr == "15000.00"


def test_unverified_scheme_is_scheme_not_verified():
    result = evaluate(program(verification_status=IncentiveVerificationStatus.PENDING_REVIEW))
    assert result.status == "scheme_not_verified"
    assert result.eligible is False


def test_inactive_scheme_is_scheme_not_active():
    result = evaluate(program(active=False))
    assert result.status == "scheme_not_active"
    assert result.eligible is False


def test_technology_mismatch_is_not_eligible():
    result = evaluate(program(technology=RenewableTechnology.WIND))
    assert result.status == "not_eligible"
    assert "wind" in result.reason.lower()


@pytest.mark.parametrize("technology", [RenewableTechnology.SOLAR, RenewableTechnology.WIND, RenewableTechnology.HYBRID, RenewableTechnology.BATTERY])
def test_matching_technology_for_each_type_is_eligible(technology):
    result = evaluate(program(technology=technology), technology=technology)
    assert result.status == "eligible"


def test_non_residential_consumer_rejected_for_residential_only_scheme():
    result = evaluate(program(), consumer_category=TariffConsumerCategory.COMMERCIAL)
    assert result.status == "not_eligible"
    assert result.eligible is False


def test_category_agnostic_scheme_applies_to_any_category():
    result = evaluate(program(consumer_category=None), consumer_category=TariffConsumerCategory.INDUSTRIAL)
    assert result.status == "eligible"


def test_capacity_below_minimum_is_not_eligible():
    result = evaluate(program(min_system_size_kw=Decimal("5")), proposed_capacity_kw=Decimal("3"))
    assert result.status == "not_eligible"


def test_capacity_exactly_at_minimum_is_eligible():
    result = evaluate(program(min_system_size_kw=Decimal("3")), proposed_capacity_kw=Decimal("3"))
    assert result.status == "eligible"


def test_capacity_above_maximum_still_eligible_but_capped_for_calculation():
    result = evaluate(
        program(subsidy_type=SubsidyType.PER_KW, subsidy_value=Decimal("10000"), max_system_size_kw=Decimal("3")),
        proposed_capacity_kw=Decimal("10"),
    )
    assert result.status == "eligible"
    # capped at 3 kW * 10000 = 30000, not 10 kW * 10000
    assert result.incentive_amount_inr == "30000.00"


def test_missing_required_field_is_insufficient_information():
    result = evaluate(
        program(eligibility_rules={"requires_fields": ["sanctioned_load_kva"]}),
    )
    assert result.status == "insufficient_information"
    assert result.missing_fields == ["sanctioned_load_kva"]


def test_present_required_field_passes_eligibility_check():
    result = evaluate(
        program(eligibility_rules={"requires_fields": ["monthly_consumption_kwh"]}),
    )
    assert result.status == "eligible"


def test_capacity_zero_is_rejected_by_minimum_check_when_min_configured():
    result = evaluate(program(min_system_size_kw=Decimal("1")), proposed_capacity_kw=Decimal("0"))
    assert result.status == "not_eligible"


def test_percentage_scheme_without_cost_basis_is_insufficient_information():
    result = evaluate(program(subsidy_type=SubsidyType.PERCENTAGE, percentage_value=Decimal("40")))
    assert result.status == "insufficient_information"
    assert "eligible_cost_basis_inr" in result.missing_fields


def test_source_metadata_is_carried_through():
    result = evaluate(
        program(source_name="TEST Ministry", source_url="https://example.invalid/x", last_verified=date(2026, 1, 1))
    )
    assert result.source.source_name == "TEST Ministry"
    assert result.source.source_url == "https://example.invalid/x"
