from datetime import date
from decimal import Decimal

from app.engines.incentive.calculator import calculate_incentive_amount
from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)
from app.schemas.incentive import IncentiveProgramInput
import uuid

BASE = dict(
    id=uuid.uuid4(),
    scheme_name="TEST FIXTURE ONLY — Scheme",
    scheme_version="TEST-V1",
    level=IncentiveLevel.CENTRAL,
    incentive_type=IncentiveType.CAPITAL_SUBSIDY,
    technology=RenewableTechnology.SOLAR,
    consumer_category=TariffConsumerCategory.RESIDENTIAL,
    effective_from=date(2026, 1, 1),
    verification_status=IncentiveVerificationStatus.VERIFIED,
    active=True,
)


def program(**overrides) -> IncentiveProgramInput:
    data = {**BASE}
    data.update(overrides)
    return IncentiveProgramInput(**data)


def test_fixed_amount_calculation():
    p = program(subsidy_type=SubsidyType.FIXED_AMOUNT, subsidy_value=Decimal("15000"))
    result = calculate_incentive_amount(p, Decimal("2"), None)
    assert result.status == "ok"
    assert result.amount_inr == Decimal("15000.00")


def test_fixed_amount_missing_value_is_insufficient_information():
    p = program(subsidy_type=SubsidyType.FIXED_AMOUNT, subsidy_value=None)
    result = calculate_incentive_amount(p, Decimal("2"), None)
    assert result.status == "insufficient_information"
    assert "subsidy_value" in result.missing_fields


def test_per_kw_calculation():
    p = program(subsidy_type=SubsidyType.PER_KW, subsidy_value=Decimal("18000"))
    result = calculate_incentive_amount(p, Decimal("2.5"), None)
    assert result.status == "ok"
    assert result.amount_inr == Decimal("45000.00")


def test_per_kw_respects_maximum_amount_cap():
    p = program(subsidy_type=SubsidyType.PER_KW, subsidy_value=Decimal("18000"), maximum_amount=Decimal("30000"))
    result = calculate_incentive_amount(p, Decimal("5"), None)
    assert result.status == "ok"
    assert result.amount_inr == Decimal("30000.00")


def test_percentage_without_cost_basis_is_insufficient_information():
    p = program(subsidy_type=SubsidyType.PERCENTAGE, percentage_value=Decimal("40"))
    result = calculate_incentive_amount(p, Decimal("3"), None)
    assert result.status == "insufficient_information"
    assert "eligible_cost_basis_inr" in result.missing_fields


def test_percentage_with_cost_basis_calculates_correctly():
    p = program(subsidy_type=SubsidyType.PERCENTAGE, percentage_value=Decimal("40"))
    result = calculate_incentive_amount(p, Decimal("3"), Decimal("200000"))
    assert result.status == "ok"
    assert result.amount_inr == Decimal("80000.00")


def test_percentage_respects_maximum_amount_cap():
    p = program(subsidy_type=SubsidyType.PERCENTAGE, percentage_value=Decimal("60"), maximum_amount=Decimal("50000"))
    result = calculate_incentive_amount(p, Decimal("3"), Decimal("200000"))
    assert result.status == "ok"
    assert result.amount_inr == Decimal("50000.00")


def test_slab_based_calculation_matches_pm_surya_ghar_style_structure():
    # TEST FIXTURE ONLY — a synthetic slab shape resembling widely-reported
    # (but NOT independently verified from an official source — see
    # backend/app/data/incentives/india/README.md) PM Surya Ghar figures.
    p = program(
        subsidy_type=SubsidyType.SLAB_BASED,
        maximum_amount=Decimal("78000"),
        calculation_rules={
            "slabs": [
                {"capacity_min_kw": 0, "capacity_max_kw": 2, "rate_inr_per_kw": 30000},
                {"capacity_min_kw": 2, "capacity_max_kw": 3, "rate_inr_per_kw": 18000},
            ]
        },
    )
    result = calculate_incentive_amount(p, Decimal("3"), None)
    assert result.status == "ok"
    # 2 kW * 30000 + 1 kW * 18000 = 78000
    assert result.amount_inr == Decimal("78000.00")


def test_slab_based_partial_capacity_within_first_slab():
    p = program(
        subsidy_type=SubsidyType.SLAB_BASED,
        calculation_rules={
            "slabs": [
                {"capacity_min_kw": 0, "capacity_max_kw": 2, "rate_inr_per_kw": 30000},
                {"capacity_min_kw": 2, "capacity_max_kw": None, "rate_inr_per_kw": 18000},
            ]
        },
    )
    result = calculate_incentive_amount(p, Decimal("1"), None)
    assert result.amount_inr == Decimal("30000.00")


def test_slab_based_missing_calculation_rules_is_insufficient_information():
    p = program(subsidy_type=SubsidyType.SLAB_BASED, calculation_rules=None)
    result = calculate_incentive_amount(p, Decimal("3"), None)
    assert result.status == "insufficient_information"
    assert "calculation_rules.slabs" in result.missing_fields


def test_benchmark_cost_based_calculation():
    p = program(
        subsidy_type=SubsidyType.BENCHMARK_COST_BASED,
        calculation_rules={"benchmark_cost_per_kw_inr": 45000, "eligible_percentage": 40},
    )
    result = calculate_incentive_amount(p, Decimal("3"), None)
    assert result.status == "ok"
    # 3 * 45000 * 0.40 = 54000
    assert result.amount_inr == Decimal("54000.00")


def test_benchmark_cost_based_missing_rules_is_insufficient_information():
    p = program(subsidy_type=SubsidyType.BENCHMARK_COST_BASED, calculation_rules=None)
    result = calculate_incentive_amount(p, Decimal("3"), None)
    assert result.status == "insufficient_information"
    assert "calculation_rules.benchmark_cost_per_kw_inr" in result.missing_fields
    assert "calculation_rules.eligible_percentage" in result.missing_fields


def test_other_subsidy_type_is_always_insufficient_information():
    p = program(subsidy_type=SubsidyType.OTHER)
    result = calculate_incentive_amount(p, Decimal("3"), None)
    assert result.status == "insufficient_information"
    assert result.notes is not None


def test_decimal_precision_is_exact():
    p = program(subsidy_type=SubsidyType.PER_KW, subsidy_value=Decimal("0.1"))
    result = calculate_incentive_amount(p, Decimal("3"), None)
    assert result.amount_inr == Decimal("0.30")
