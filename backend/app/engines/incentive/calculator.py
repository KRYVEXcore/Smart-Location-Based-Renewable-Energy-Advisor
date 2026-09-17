"""Deterministic incentive-amount calculation.

All money math uses Decimal — never float. Every calculation type either
produces a definite amount from data the programme actually documents, or
reports exactly which input is missing ("insufficient_information") —
never a guessed or zero-substituted amount.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from app.engines.incentive.validation import CapacitySlab, validate_capacity_slabs
from app.models.enums import SubsidyType
from app.schemas.incentive import IncentiveProgramInput

TWO_PLACES = Decimal("0.01")

CalculationStatus = Literal["ok", "insufficient_information"]


@dataclass(frozen=True)
class CalculationResult:
    status: CalculationStatus
    amount_inr: Decimal | None
    missing_fields: list[str]
    notes: str | None = None


def parse_capacity_slabs(calculation_rules: dict | None) -> list[CapacitySlab] | None:
    """Public: also used by scripts/seed_incentives.py to validate
    slab_based scheme data before writing it to the database.
    """
    if not calculation_rules or not calculation_rules.get("slabs"):
        return None
    return [
        CapacitySlab(
            capacity_min_kw=Decimal(str(slab["capacity_min_kw"])),
            capacity_max_kw=(
                None if slab.get("capacity_max_kw") is None else Decimal(str(slab["capacity_max_kw"]))
            ),
            rate_inr_per_kw=Decimal(str(slab["rate_inr_per_kw"])),
        )
        for slab in calculation_rules["slabs"]
    ]


def _calculate_slab_amount(capacity_kw: Decimal, slabs: list[CapacitySlab]) -> Decimal:
    validate_capacity_slabs(slabs)

    if capacity_kw <= Decimal("0"):
        return Decimal("0.00")

    total = Decimal("0")
    for slab in sorted(slabs, key=lambda slab: slab.capacity_min_kw):
        if capacity_kw <= slab.capacity_min_kw:
            continue
        upper_bound = capacity_kw if slab.capacity_max_kw is None else min(capacity_kw, slab.capacity_max_kw)
        total += (upper_bound - slab.capacity_min_kw) * slab.rate_inr_per_kw

    return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_incentive_amount(
    program: IncentiveProgramInput,
    eligible_capacity_kw: Decimal,
    eligible_cost_basis_inr: Decimal | None,
) -> CalculationResult:
    """`eligible_capacity_kw` is the proposed capacity already capped at
    the programme's max_system_size_kw, if any — see
    app.engines.incentive.eligibility, which computes it before calling
    here. `eligible_cost_basis_inr` is None today: this app collects no
    verified installation cost (a user's own aspirational budget is not a
    vendor quotation) — see the README's Phase 6 boundary notes. That
    makes PERCENTAGE and BENCHMARK_COST_BASED always
    "insufficient_information" for now, honestly, rather than inventing a
    cost basis.
    """
    if program.subsidy_type == SubsidyType.FIXED_AMOUNT:
        if program.subsidy_value is None:
            return CalculationResult("insufficient_information", None, ["subsidy_value"])
        amount = program.subsidy_value

    elif program.subsidy_type == SubsidyType.PER_KW:
        if program.subsidy_value is None:
            return CalculationResult("insufficient_information", None, ["subsidy_value"])
        amount = eligible_capacity_kw * program.subsidy_value

    elif program.subsidy_type == SubsidyType.SLAB_BASED:
        slabs = parse_capacity_slabs(program.calculation_rules)
        if slabs is None:
            return CalculationResult("insufficient_information", None, ["calculation_rules.slabs"])
        amount = _calculate_slab_amount(eligible_capacity_kw, slabs)

    elif program.subsidy_type == SubsidyType.PERCENTAGE:
        missing = [
            field
            for field, value in (
                ("eligible_cost_basis_inr", eligible_cost_basis_inr),
                ("percentage_value", program.percentage_value),
            )
            if value is None
        ]
        if missing:
            return CalculationResult("insufficient_information", None, missing)
        amount = (eligible_cost_basis_inr * program.percentage_value / Decimal("100")).quantize(TWO_PLACES)

    elif program.subsidy_type == SubsidyType.BENCHMARK_COST_BASED:
        rules = program.calculation_rules or {}
        benchmark_cost_per_kw = rules.get("benchmark_cost_per_kw_inr")
        eligible_percentage = rules.get("eligible_percentage")
        missing = [
            field
            for field, value in (
                ("calculation_rules.benchmark_cost_per_kw_inr", benchmark_cost_per_kw),
                ("calculation_rules.eligible_percentage", eligible_percentage),
            )
            if value is None
        ]
        if missing:
            return CalculationResult("insufficient_information", None, missing)
        amount = (
            eligible_capacity_kw * Decimal(str(benchmark_cost_per_kw)) * Decimal(str(eligible_percentage))
            / Decimal("100")
        ).quantize(TWO_PLACES)

    else:  # SubsidyType.OTHER — no formula this engine can execute automatically.
        return CalculationResult(
            "insufficient_information",
            None,
            [],
            notes="This programme's calculation method has no automatic formula in this engine.",
        )

    if program.maximum_amount is not None:
        amount = min(amount, program.maximum_amount)

    return CalculationResult("ok", amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), [])
