from datetime import date
from decimal import Decimal

from app.engines.tariff.tariff_engine import calculate_bill_for_grid_consumption
from app.engines.tariff.version import ENGINE_CALCULATION_VERSION
from app.models.enums import TariffConsumerCategory
from app.schemas.tariff import TariffSlabInput

BASE = dict(
    tariff_version="TEST-V1",
    tariff_name="TEST Domestic Tariff",
    effective_from=date(2026, 1, 1),
)

CANDIDATE_ROWS = [
    TariffSlabInput(**BASE, slab_min_kwh=Decimal("0"), slab_max_kwh=Decimal("100"), energy_charge_inr_per_kwh=Decimal("3.00")),
    TariffSlabInput(**BASE, slab_min_kwh=Decimal("100"), slab_max_kwh=None, energy_charge_inr_per_kwh=Decimal("5.00"), fixed_charge_inr=Decimal("50.00")),
]


def test_calculate_returns_ok_with_full_breakdown():
    result = calculate_bill_for_grid_consumption(
        Decimal("250"), CANDIDATE_ROWS, date(2026, 6, 1), TariffConsumerCategory.RESIDENTIAL
    )

    assert result.status == "ok"
    assert result.reason is None
    assert result.tariff.tariff_version == "TEST-V1"
    assert result.consumer_category == TariffConsumerCategory.RESIDENTIAL
    # 100 @ 3.00 + 150 @ 5.00 = 300 + 750 = 1050.00, + fixed 50.00 = 1100.00
    assert result.estimated_monthly_bill_inr == "1100.00"
    assert result.calculation_version == ENGINE_CALCULATION_VERSION


def test_calculate_reports_tariff_not_configured_when_no_version_covers_the_date():
    result = calculate_bill_for_grid_consumption(
        Decimal("250"), CANDIDATE_ROWS, date(2020, 1, 1), TariffConsumerCategory.RESIDENTIAL
    )

    assert result.status == "tariff_not_configured"
    assert result.reason is not None
    assert result.tariff is None
    assert result.estimated_monthly_bill_inr is None


def test_calculate_marks_demand_and_tod_as_excluded_components():
    result = calculate_bill_for_grid_consumption(
        Decimal("250"), CANDIDATE_ROWS, date(2026, 6, 1), TariffConsumerCategory.RESIDENTIAL
    )

    assert "demand_charge_not_calculated" in result.excluded_components
    assert "tod_charge_not_calculated" in result.excluded_components
    assert result.is_partial_estimate is True


def test_calculate_never_includes_subsidy_savings_or_payback_fields():
    result = calculate_bill_for_grid_consumption(
        Decimal("250"), CANDIDATE_ROWS, date(2026, 6, 1), TariffConsumerCategory.RESIDENTIAL
    )

    dumped = result.model_dump()
    assert "subsidy" not in dumped
    assert "savings" not in dumped
    assert "payback" not in dumped


def test_calculate_is_reproducible_for_identical_input():
    first = calculate_bill_for_grid_consumption(
        Decimal("250"), CANDIDATE_ROWS, date(2026, 6, 1), TariffConsumerCategory.RESIDENTIAL
    )
    second = calculate_bill_for_grid_consumption(
        Decimal("250"), CANDIDATE_ROWS, date(2026, 6, 1), TariffConsumerCategory.RESIDENTIAL
    )

    assert first.estimated_monthly_bill_inr == second.estimated_monthly_bill_inr
    assert first.charges == second.charges
