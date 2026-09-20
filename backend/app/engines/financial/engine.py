"""Financial Analysis Engine: estimated cost, incentive, net investment, savings and simple payback
for the system the Recommendation Engine chose. Cost comes from the verified cost dataset, the
incentive from the existing Incentive Engine (via the recommendation), and savings from the existing
Tariff Engine. Nothing is invented: a value that cannot be supported is None (never zero), and no AI
is involved. Given the same inputs it always returns the same analysis (only `calculated_at` differs).
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.engines.financial.costs import gross_cost
from app.engines.recommendation.assumptions import BUDGET_UNAVAILABLE_NOTE, COST_UNAVAILABLE_NOTE
from app.schemas.financial import CostBenchmarkRecord, FinancialAnalysisResult
from app.schemas.recommendation import CostContext, InrRange, RecommendationResult, YearsRange

FINANCIAL_VERSION = "financial-2026.1"

COST_AVAILABLE_NOTE = (
    "Estimated figures: the cost is a published MNRE benchmark, not a vendor quote, and savings and payback "
    "are modelled estimates, not guarantees."
)

METHODOLOGY = [
    "Gross cost: the verified benchmark cost for exactly the recommended capacity (per-kW tiers), from the cost dataset.",
    "Incentive: the verified incentive the existing Incentive Engine returned for the recommended system; if several apply and "
    "combining them is not verified, only the largest is applied.",
    "Net investment: gross cost minus that incentive, never below zero.",
    "Savings: for each month, the existing Tariff Engine bill for the customer's consumption minus the bill for the consumption "
    "left after solar generation (limited to what the customer uses). Surplus generation is not valued.",
    "Estimated simple payback: net investment divided by estimated annual savings, only when both exist and savings are above zero.",
]

STANDING_LIMITATIONS = [
    "Export or net-metering compensation is not modelled: surplus generation is not valued at the retail tariff or at all.",
    "Simple payback excludes tariff escalation, maintenance savings, financing or loan costs, tax benefits, panel degradation and any future return on investment.",
    "Consumption is treated as the same every month. Demand and time-of-day charges, government bill subsidies, taxes, duties and surcharges are not modelled.",
    "These are estimates for planning, not guarantees of cost, savings or payback.",
]

_MONTHS = 12

# tariff bill (rupees) for a monthly consumption in kWh, or None if it cannot be calculated
BillAt = Callable[[Decimal], Decimal | None]


@dataclass(frozen=True)
class FinancialInput:
    recommendation: RecommendationResult
    state: str | None
    consumer_category: str | None
    monthly_consumption_kwh: float | None
    monthly_generation_kwh: dict[str, float] | None  # of the recommended solar option
    bill_at: BillAt | None  # None when no verified applicable tariff exists
    tariff_name: str | None = None
    tariff_version: str | None = None
    cost_records: Sequence[CostBenchmarkRecord] = ()


def analyse(engine_input: FinancialInput) -> FinancialAnalysisResult:
    rec = engine_input.recommendation
    common = {
        "assessment_id": rec.assessment_id,
        "methodology": METHODOLOGY,
        "calculation_version": FINANCIAL_VERSION,
        "calculated_at": datetime.now(UTC),
    }
    capacity = rec.recommended_capacity_kw
    if rec.recommendation_status != "recommended" or capacity is None:
        return FinancialAnalysisResult(
            status="insufficient_data" if rec.recommendation_status == "insufficient_data" else "not_applicable",
            reason=f"There is no recommended system to analyse financially. {rec.recommendation_reason}",
            **common,
        )
    if rec.recommended_technology != "solar":
        return FinancialAnalysisResult(
            status="insufficient_data",
            reason="Cost and savings are only modelled for rooftop solar, and no verified cost data exists for this technology.",
            technology=rec.recommended_technology,
            capacity_kw=capacity,
            **common,
        )

    limitations = list(STANDING_LIMITATIONS)
    cost = gross_cost(engine_input.cost_records, capacity, engine_input.state, engine_input.consumer_category)
    gross_range, basis = cost if cost else (None, None)
    if basis is None:
        limitations.insert(0, COST_UNAVAILABLE_NOTE)
    elif capacity > 3:
        limitations.append(
            "The MNRE guideline defines central financial assistance up to 3 kW; its per-kW benchmark rates are applied here "
            f"to the full {capacity:g} kW."
        )

    incentive_inr, scheme, incentive_note = _incentive(rec)
    net_range = _net(gross_range, incentive_inr)
    savings = _savings(engine_input)

    annual = savings["annual"] if savings else None
    status = _status(basis is not None, savings is not None)
    payback, payback_note = _payback(net_range, annual)

    return FinancialAnalysisResult(
        status=status,
        reason=_reason(status),
        technology="solar",
        capacity_kw=capacity,
        cost_status="available" if basis else "not_available",
        gross_cost_range_inr=gross_range,
        cost_basis=basis,
        incentive_inr=incentive_inr,
        incentive_scheme=scheme,
        incentive_note=incentive_note,
        net_investment_range_inr=net_range,
        savings_status="available" if savings else "not_available",
        annual_savings_inr=annual,
        monthly_savings_inr=round(annual / _MONTHS, 2) if annual is not None else None,
        baseline_annual_bill_inr=savings["before"] if savings else None,
        annual_bill_after_solar_inr=savings["after"] if savings else None,
        annual_self_consumed_kwh=savings["used"] if savings else None,
        annual_surplus_generation_kwh=savings["surplus"] if savings else None,
        tariff_name=engine_input.tariff_name if savings else None,
        tariff_version=engine_input.tariff_version if savings else None,
        simple_payback_years_range=payback,
        payback_note=payback_note,
        limitations=limitations,
        **common,
    )


def cost_context_for(analysis: FinancialAnalysisResult, budget_inr: float | None) -> CostContext:
    """How the recommendation shows the analysis. Without verified cost the two existing messages
    are kept exactly (with or without a budget); savings are still shown when they were modelled."""
    has_cost = analysis.cost_status == "available"
    return CostContext(
        status="available" if has_cost else "not_available",
        budget_inr=budget_inr,
        note=COST_AVAILABLE_NOTE if has_cost else (BUDGET_UNAVAILABLE_NOTE if budget_inr else COST_UNAVAILABLE_NOTE),
        installed_cost_range_inr=analysis.gross_cost_range_inr,
        incentive_inr=analysis.incentive_inr,
        net_investment_range_inr=analysis.net_investment_range_inr,
        annual_savings_inr=analysis.annual_savings_inr,
        monthly_savings_inr=analysis.monthly_savings_inr,
        simple_payback_years_range=analysis.simple_payback_years_range,
    )


def _incentive(rec: RecommendationResult) -> tuple[float | None, str | None, str]:
    eligible = [(float(i.incentive_amount_inr), i) for i in rec.applicable_incentives if i.incentive_amount_inr is not None]
    if not eligible:
        note = rec.incentive_context.note if rec.incentive_context else "No verified incentive is available for this system."
        return None, None, note
    amount, chosen = max(eligible, key=lambda pair: pair[0])
    if len(eligible) > 1:
        return amount, chosen.scheme_name, (
            f"{len(eligible)} verified programmes apply, but combining them is not verified, so only the largest "
            f"({chosen.scheme_name}) is applied."
        )
    return amount, chosen.scheme_name, f"{chosen.scheme_name}, as calculated by the verified incentive data."


def _net(gross: InrRange | None, incentive_inr: float | None) -> InrRange | None:
    if gross is None:
        return None
    deduction = incentive_inr or 0.0
    return InrRange(low=round(max(gross.low - deduction, 0.0), 2), high=round(max(gross.high - deduction, 0.0), 2))


def _savings(engine_input: FinancialInput) -> dict[str, float] | None:
    """Annual bill with and without solar under the verified tariff, or None if it cannot be modelled."""
    bill_at, monthly = engine_input.bill_at, engine_input.monthly_generation_kwh
    consumption = engine_input.monthly_consumption_kwh
    if bill_at is None or consumption is None or consumption <= 0 or not monthly or len(monthly) != _MONTHS:
        return None
    use = Decimal(str(consumption))
    baseline = bill_at(use)
    if baseline is None:
        return None
    before = after = used = surplus = Decimal(0)
    for generation in monthly.values():
        generated = Decimal(str(generation))
        offset = min(generated, use)  # only consumption that solar actually replaces earns a saving
        remaining = bill_at(use - offset)
        if remaining is None:
            return None
        before += baseline
        after += remaining
        used += offset
        surplus += generated - offset
    return {
        "annual": round(float(before - after), 2),
        "before": round(float(before), 2),
        "after": round(float(after), 2),
        "used": round(float(used), 1),
        "surplus": round(float(surplus), 1),
    }


def _payback(net: InrRange | None, annual_savings: float | None) -> tuple[YearsRange | None, str | None]:
    if net is None:
        return None, "Payback is not calculated because the net investment is not available."
    if annual_savings is None:
        return None, "Payback is not calculated because savings cannot be modelled from verified data."
    if annual_savings <= 0:
        return None, "Payback is not calculated because the modelled savings are not above zero."
    return (
        YearsRange(low=round(net.low / annual_savings, 1), high=round(net.high / annual_savings, 1)),
        "Estimated simple payback = net investment / estimated annual savings.",
    )


def _status(has_cost: bool, has_savings: bool) -> str:
    if has_cost and has_savings:
        return "complete"
    if has_savings:
        return "cost_unavailable"
    if has_cost:
        return "savings_unavailable"
    return "insufficient_data"


def _reason(status: str) -> str | None:
    return {
        "cost_unavailable": "Verified system cost data is not available for this system, so net investment and payback cannot be calculated.",
        "savings_unavailable": "Savings cannot be modelled because a verified applicable tariff or the monthly generation is not available.",
        "insufficient_data": "Neither a verified cost nor modelled savings is available for this system.",
    }.get(status)

