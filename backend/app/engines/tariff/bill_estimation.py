"""Estimates monthly consumption from a customer's monthly electricity bill.

The bill is NOT divided by a per-unit rate: Indian bills combine slabs, fixed charges and
other components. Instead the EXISTING Tariff Engine is evaluated at candidate consumption
values and a bounded bisection finds the consumption whose modelled bill matches the entered
one. No tariff formula lives here.

The result is an estimate. Anything the tariff model cannot express (duty, taxes, surcharges,
per-kW fixed charges) is stated as a limitation, never guessed.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from app.engines.tariff.tariff_engine import calculate_bill_for_grid_consumption
from app.models.enums import TariffConsumerCategory
from app.schemas.consumption import BillConsumptionEstimate
from app.schemas.tariff import TariffCalculationResponse, TariffSlabInput

METHOD = (
    "Evaluated the verified tariff (the existing Tariff Engine) at candidate consumption values "
    "until the modelled bill matched the entered bill (bounded bisection). The bill was not divided "
    "by a per-unit rate."
)

# A modelled bill within this many rupees of the entered bill counts as a match.
BILL_TOLERANCE_INR = Decimal("1.00")
# Search precision and ceiling for monthly consumption (kWh), matching the assessment input limit.
PRECISION_KWH = Decimal("0.01")
MAX_MONTHLY_KWH = Decimal("500000")
MAX_ITERATIONS = 80

BASE_LIMITATION = (
    "This is an estimate, not a meter reading. A real bill can include charges this tariff model does "
    "not cover (for example electricity duty, taxes or surcharges), so actual consumption may differ."
)


def estimate_consumption_from_bill(
    bill_inr: Decimal,
    rows: list[TariffSlabInput],
    calculation_date: date,
    consumer_category: TariffConsumerCategory,
) -> BillConsumptionEstimate:
    def bill_at(kwh: Decimal) -> tuple[Decimal | None, TariffCalculationResponse]:
        result = calculate_bill_for_grid_consumption(kwh, rows, calculation_date, consumer_category)
        if result.status != "ok" or result.estimated_monthly_bill_inr is None:
            return None, result
        return Decimal(result.estimated_monthly_bill_inr), result

    def unavailable(reason: str, schedule: TariffCalculationResponse | None = None) -> BillConsumptionEstimate:
        return _build(bill_inr, "insufficient_data", schedule, reason=reason)

    at_zero, zero_result = bill_at(Decimal(0))
    if at_zero is None:
        return unavailable(zero_result.reason or "The applicable tariff could not be evaluated.")
    if bill_inr < at_zero:
        return unavailable(
            f"The entered bill is lower than the minimum charge in the applicable tariff (about "
            f"₹{at_zero:,.2f}), so consumption cannot be estimated from it.",
            zero_result,
        )
    at_max, _ = bill_at(MAX_MONTHLY_KWH)
    if at_max is None or bill_inr > at_max:
        return unavailable("The entered bill is higher than the applicable tariff can explain.", zero_result)

    # Largest consumption whose modelled bill does not exceed the entered bill.
    low, high = Decimal(0), MAX_MONTHLY_KWH
    for _ in range(MAX_ITERATIONS):
        if high - low <= PRECISION_KWH:
            break
        middle = (low + high) / 2
        modelled, _ = bill_at(middle)
        if modelled is not None and modelled <= bill_inr:
            low = middle
        else:
            high = middle
    lowest_match = low
    modelled_low, result = bill_at(lowest_match)
    assert modelled_low is not None

    if bill_inr - modelled_low <= BILL_TOLERANCE_INR:
        return _build(bill_inr, "estimated", result, kwh=lowest_match, match="within_tolerance")

    # The entered bill falls in a jump of the tariff (a fixed charge that steps up between brackets):
    # no consumption produces it exactly. Report the range between the two sides of the jump.
    low2, high2 = lowest_match, MAX_MONTHLY_KWH
    for _ in range(MAX_ITERATIONS):
        if high2 - low2 <= PRECISION_KWH:
            break
        middle = (low2 + high2) / 2
        modelled, _ = bill_at(middle)
        if modelled is not None and modelled < bill_inr:
            low2 = middle
        else:
            high2 = middle
    return _build(
        bill_inr,
        "estimated",
        result,
        kwh=(lowest_match + high2) / 2,
        low=lowest_match,
        high=high2,
        match="fixed_charge_gap",
    )


def unavailable_estimate(bill_inr: Decimal, reason: str) -> BillConsumptionEstimate:
    """No verified applicable tariff could be established, so nothing is estimated."""
    return _build(bill_inr, "insufficient_data", None, reason=reason)


def _build(
    bill_inr: Decimal,
    status: str,
    result: TariffCalculationResponse | None,
    *,
    reason: str | None = None,
    kwh: Decimal | None = None,
    low: Decimal | None = None,
    high: Decimal | None = None,
    match: str | None = None,
) -> BillConsumptionEstimate:
    schedule = result.tariff if result is not None else None
    excluded = list(result.excluded_components) if result is not None and result.status == "ok" else []
    limitations = [BASE_LIMITATION] if status == "estimated" else []
    if excluded:
        limitations.append(
            "The tariff has components this app cannot calculate (" + ", ".join(excluded) + "), so the estimate may be off."
        )
    if match == "fixed_charge_gap":
        limitations.append(
            "The entered bill falls between two fixed-charge brackets, so a range is shown and the estimate is its midpoint."
        )
    return BillConsumptionEstimate(
        status=status,  # type: ignore[arg-type]
        reason=reason,
        monthly_bill_inr=float(bill_inr),
        estimated_monthly_consumption_kwh=None if kwh is None else _one_decimal(kwh),
        range_low_kwh=None if low is None else _one_decimal(low),
        range_high_kwh=None if high is None else _one_decimal(high),
        match=match,  # type: ignore[arg-type]
        method=METHOD,
        tariff_name=schedule.tariff_name if schedule else None,
        tariff_version=schedule.tariff_version if schedule else None,
        tariff_effective_from=schedule.effective_from if schedule else None,
        excluded_components=excluded,
        limitations=limitations,
        estimated_at=datetime.now(UTC),
    )


def _one_decimal(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.1")))
