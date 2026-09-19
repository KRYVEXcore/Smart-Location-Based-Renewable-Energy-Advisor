"""Deterministic eligibility evaluation for a single incentive programme.

Assumes a scheme version has already been selected for the calculation
date (see version_selection.py) — this checks verification status,
active flag, technology match, consumer-category match, capacity bounds,
and any documented eligibility_rules, then delegates amount calculation to
calculator.py. Never guesses a value this app doesn't collect: a
requirement this app can't check comes back as "insufficient_information"
with the exact missing field names.
"""

from decimal import Decimal

from app.engines.incentive.calculator import calculate_incentive_amount
from app.models.enums import IncentiveVerificationStatus, RenewableTechnology, TariffConsumerCategory
from app.schemas.incentive import IncentiveEligibilityResult, IncentiveProgramInput, IncentiveSourceInfo


def evaluate_program_eligibility(
    program: IncentiveProgramInput,
    *,
    technology: RenewableTechnology,
    consumer_category: TariffConsumerCategory,
    proposed_capacity_kw: Decimal,
    eligible_cost_basis_inr: Decimal | None,
    available_context: dict[str, object],
) -> IncentiveEligibilityResult:
    base = dict(
        scheme_name=program.scheme_name,
        scheme_version=program.scheme_version,
        level=program.level,
        incentive_type=program.incentive_type,
        technology=program.technology,
        source=IncentiveSourceInfo(
            source_name=program.source_name,
            source_url=program.source_url,
            source_document=program.source_document,
            source_order_number=program.source_order_number,
            source_order_date=program.source_order_date,
            source_page=program.source_page,
            source_table=program.source_table,
            source_section=program.source_section,
            source_excerpt=program.source_excerpt,
            verification_notes=program.verification_notes,
            verification_status=program.verification_status,
            last_verified=program.last_verified,
        ),
        effective_from=program.effective_from,
        effective_to=program.effective_to,
    )

    if program.verification_status != IncentiveVerificationStatus.VERIFIED:
        return IncentiveEligibilityResult(
            **base,
            status="scheme_not_verified",
            eligible=False,
            reason=(
                "This programme was found, but its current applicability could not be "
                f"verified against an official source (status: {program.verification_status.value})."
            ),
        )

    if not program.active:
        return IncentiveEligibilityResult(
            **base, status="scheme_not_active", eligible=False, reason="This programme is marked inactive."
        )

    if program.technology != technology:
        return IncentiveEligibilityResult(
            **base,
            status="not_eligible",
            eligible=False,
            reason=f"This programme applies to {program.technology.value}, not {technology.value}.",
        )

    if program.consumer_category is not None and program.consumer_category != consumer_category:
        return IncentiveEligibilityResult(
            **base,
            status="not_eligible",
            eligible=False,
            reason=(
                f"This programme applies to {program.consumer_category.value} consumers, "
                f"not {consumer_category.value}."
            ),
        )

    if program.min_system_size_kw is not None and proposed_capacity_kw < program.min_system_size_kw:
        return IncentiveEligibilityResult(
            **base,
            status="not_eligible",
            eligible=False,
            reason=f"Requires at least {program.min_system_size_kw} kW; {proposed_capacity_kw} kW proposed.",
        )

    missing = _missing_required_fields(program.eligibility_rules, available_context)
    if missing:
        return IncentiveEligibilityResult(
            **base,
            status="insufficient_information",
            eligible=False,
            reason="More information is required to determine eligibility for this programme.",
            missing_fields=missing,
        )

    # Capacity above the programme's cap doesn't disqualify the system —
    # it just limits how much of it counts toward this programme's amount
    # (e.g. PM Surya Ghar's CFA caps at 3 kW even for a larger system).
    eligible_capacity_kw = (
        min(proposed_capacity_kw, program.max_system_size_kw)
        if program.max_system_size_kw is not None
        else proposed_capacity_kw
    )

    calculation = calculate_incentive_amount(program, eligible_capacity_kw, eligible_cost_basis_inr)

    if calculation.status == "insufficient_information":
        return IncentiveEligibilityResult(
            **base,
            status="insufficient_information",
            eligible=False,
            reason=(
                "This programme's rules appear to apply, but its exact amount cannot be "
                "calculated from the data available."
            ),
            missing_fields=calculation.missing_fields,
            calculation_notes=calculation.notes,
        )

    return IncentiveEligibilityResult(
        **base,
        status="eligible",
        eligible=True,
        reason="Eligible based on the verified scheme rules.",
        incentive_amount_inr=str(calculation.amount_inr) if calculation.amount_inr is not None else None,
        eligible_cost_basis_inr=str(eligible_cost_basis_inr) if eligible_cost_basis_inr is not None else None,
    )


def _missing_required_fields(eligibility_rules: dict | None, available_context: dict[str, object]) -> list[str]:
    """A field the assessment never collects at all (not present as a key
    in available_context) always resolves as missing — this app never
    invents data it doesn't have, regardless of what a scheme requires.
    """
    if not eligibility_rules:
        return []
    required_fields = eligibility_rules.get("requires_fields") or []
    return [field for field in required_fields if available_context.get(field) is None]
