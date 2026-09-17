"""Incentive Engine entry point.

Pure calculation: given candidate incentive programme rows already scoped
to the requested technology/category and state-or-UT (see
app.services.incentive_evaluation_service — this module never touches the
database, FastAPI, or a location provider, and never receives a
DISCOM-level programme for an ambiguous/unidentified DISCOM, since the
service never guesses one), groups them into distinct schemes, selects the
version applicable on calculation_date, evaluates eligibility, computes
amounts, and flags stacking uncertainty.

No final installation cost, final savings, payback, or ROI is computed
here — see the README's Phase 6 boundary notes.
"""

from datetime import date
from decimal import Decimal

from app.engines.incentive.eligibility import evaluate_program_eligibility
from app.engines.incentive.stacking import apply_stacking_rules
from app.engines.incentive.version_selection import group_by_scheme, select_scheme_version
from app.models.enums import RenewableTechnology, TariffConsumerCategory
from app.schemas.incentive import IncentiveEligibilityResult, IncentiveProgramInput


def evaluate_incentives(
    candidate_rows: list[IncentiveProgramInput],
    *,
    calculation_date: date,
    technology: RenewableTechnology,
    consumer_category: TariffConsumerCategory,
    proposed_capacity_kw: Decimal,
    eligible_cost_basis_inr: Decimal | None,
    available_context: dict[str, object],
) -> list[IncentiveEligibilityResult]:
    grouped = group_by_scheme(candidate_rows)
    evaluated: list[tuple[IncentiveProgramInput, IncentiveEligibilityResult]] = []

    for (scheme_name, level, scheme_technology), scheme_rows in grouped.items():
        selection = select_scheme_version(scheme_rows, calculation_date)

        if selection.status != "ok" or selection.row is None:
            evaluated.append(
                (
                    scheme_rows[0],
                    IncentiveEligibilityResult(
                        scheme_name=scheme_name,
                        level=level,
                        technology=scheme_technology,
                        status=selection.status,
                        eligible=False,
                        reason=(
                            "No configured version of this programme covers the requested date "
                            f"({calculation_date.isoformat()})."
                        ),
                    ),
                )
            )
            continue

        row = selection.row
        result = evaluate_program_eligibility(
            row,
            technology=technology,
            consumer_category=consumer_category,
            proposed_capacity_kw=proposed_capacity_kw,
            eligible_cost_basis_inr=eligible_cost_basis_inr,
            available_context=available_context,
        )
        evaluated.append((row, result))

    return apply_stacking_rules(evaluated)
