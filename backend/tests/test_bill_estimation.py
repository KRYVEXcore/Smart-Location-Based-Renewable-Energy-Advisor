"""Bill -> consumption estimate. The estimator only ever evaluates the EXISTING Tariff Engine
(slabs, fixed charges), so these tests build tariffs from TEST FIXTURE slab rows and compare
against that same engine - never against a hand-written formula or a bill / rate division.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.engines.tariff.bill_estimation import BASE_LIMITATION, estimate_consumption_from_bill, unavailable_estimate
from app.engines.tariff.tariff_engine import calculate_bill_for_grid_consumption
from app.models.enums import FixedChargeBasis, TariffConsumerCategory
from app.schemas.tariff import TariffSlabInput

TODAY = date(2026, 9, 20)
CATEGORY = TariffConsumerCategory.RESIDENTIAL


def slab(lo, hi, rate, fixed, basis=FixedChargeBasis.INR_PER_MONTH, effective_from=date(2026, 1, 1)):
    return TariffSlabInput(
        tariff_version="TEST-1",
        tariff_name="TEST FIXTURE ONLY tariff",
        slab_min_kwh=Decimal(lo),
        slab_max_kwh=None if hi is None else Decimal(hi),
        energy_charge_inr_per_kwh=Decimal(rate),
        fixed_charge_inr=None if fixed is None else Decimal(fixed),
        fixed_charge_basis=basis if fixed is not None else None,
        effective_from=effective_from,
    )


# 0-100 @ 2, 100-200 @ 4, above 200 @ 6; fixed charge 50, 50, then 100 (a step up above 200 kWh).
STEPPED = [slab(0, 100, 2, 50), slab(100, 200, 4, 50), slab(200, None, 6, 100)]
FLAT = [slab(0, None, 5, 100)]


def modelled_bill(kwh, rows=STEPPED):
    result = calculate_bill_for_grid_consumption(Decimal(str(kwh)), rows, TODAY, CATEGORY)
    return Decimal(result.estimated_monthly_bill_inr)


def estimate(bill, rows=STEPPED):
    return estimate_consumption_from_bill(Decimal(str(bill)), rows, TODAY, CATEGORY)


def test_the_estimate_matches_the_existing_tariff_engine_not_a_division():
    result = estimate(500)

    assert result.status == "estimated" and result.match == "within_tolerance"
    assert abs(modelled_bill(result.estimated_monthly_consumption_kwh) - Decimal(500)) <= 1
    # Slabs + fixed charge make the answer differ from any single-rate division of the bill.
    for rate in (2, 4, 6):
        assert result.estimated_monthly_consumption_kwh != pytest.approx(500 / rate, abs=1)
    assert result.estimated_monthly_consumption_kwh == pytest.approx(162.5, abs=0.2)


def test_fixed_charge_is_part_of_the_match():
    with_fixed = estimate(1000, FLAT)
    without_fixed = estimate(1000, [slab(0, None, 5, None)])

    assert with_fixed.estimated_monthly_consumption_kwh == pytest.approx(180.0, abs=0.2)  # (1000 - 100) / 5 via the engine
    assert without_fixed.estimated_monthly_consumption_kwh == pytest.approx(200.0, abs=0.2)


@pytest.mark.parametrize("kwh", [0.5, 30, 100, 137.4, 250, 611.3, 1999.9])
def test_estimating_a_modelled_bill_recovers_the_consumption(kwh):
    bill = modelled_bill(kwh)

    result = estimate(bill)

    assert result.status == "estimated"
    assert abs(modelled_bill(result.estimated_monthly_consumption_kwh) - bill) <= 1


def test_a_bill_inside_a_fixed_charge_jump_gives_a_range_not_a_false_exact_match():
    # 650 is the bill at 200 kWh; just above 200 kWh the fixed charge steps up by 50, so 670 is unreachable.
    result = estimate(670)

    assert result.status == "estimated" and result.match == "fixed_charge_gap"
    assert result.range_low_kwh <= result.estimated_monthly_consumption_kwh <= result.range_high_kwh
    assert result.estimated_monthly_consumption_kwh == pytest.approx(200, abs=0.2)
    assert any("between two fixed-charge brackets" in limit for limit in result.limitations)


def test_a_bill_below_the_minimum_charge_is_insufficient_data():
    result = estimate(30)

    assert result.status == "insufficient_data"
    assert result.estimated_monthly_consumption_kwh is None
    assert "minimum charge" in result.reason


def test_a_tariff_that_does_not_cover_today_is_insufficient_data():
    future = [slab(0, None, 5, 100, effective_from=date(2030, 1, 1))]

    result = estimate(1000, future)

    assert result.status == "insufficient_data" and result.estimated_monthly_consumption_kwh is None
    assert result.reason


def test_components_the_tariff_model_cannot_calculate_are_stated():
    per_kw = [slab(0, None, 5, 90, basis=FixedChargeBasis.INR_PER_KW_PER_MONTH)]

    result = estimate(1000, per_kw)

    assert result.status == "estimated"
    assert "fixed_charge_not_calculated" in result.excluded_components
    assert any("cannot calculate" in limit for limit in result.limitations)


def test_an_estimate_is_labelled_as_an_estimate_never_a_meter_reading():
    result = estimate(500)

    assert result.source == "user_bill_estimate"
    assert BASE_LIMITATION in result.limitations
    assert "not a meter reading" in BASE_LIMITATION
    assert "not divided by a per-unit rate" in result.method
    assert result.tariff_name == "TEST FIXTURE ONLY tariff" and result.tariff_version == "TEST-1"


def test_no_verified_tariff_means_nothing_is_estimated():
    result = unavailable_estimate(Decimal(7500), "Bill-based consumption estimate unavailable for this location.")

    assert result.status == "insufficient_data"
    assert result.estimated_monthly_consumption_kwh is None and result.range_low_kwh is None
    assert result.monthly_bill_inr == 7500


def test_the_same_bill_always_gives_the_same_estimate():
    first, second = estimate(7500), estimate(7500)

    assert first.model_dump(exclude={"estimated_at"}) == second.model_dump(exclude={"estimated_at"})


def test_different_bills_give_different_estimates():
    assert estimate(3000).estimated_monthly_consumption_kwh < estimate(7500).estimated_monthly_consumption_kwh


def test_the_estimator_contains_no_bill_over_rate_division():
    source = Path("app/engines/tariff/bill_estimation.py").read_text(encoding="utf-8")
    code = "\n".join(line for line in source.splitlines() if not line.strip().startswith(("#", '"', "'")))

    assert "bill_inr /" not in code and "/ rate" not in code and "per_kwh" not in code.lower()
