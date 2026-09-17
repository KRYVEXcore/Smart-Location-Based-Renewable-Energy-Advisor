"""Combinability ("stacking") checks across simultaneously-eligible
incentive programmes.

This never sums multiple programmes into one total — each stays a
separate line item in the response — and never assumes two eligible
incentives can be combined just because both are individually eligible.
See IncentiveProgram.stacking_rules: absent or incomplete rules on either
side mean "unverified", not "combinable by default".

Expected stacking_rules shape (all keys optional):
    {
        "combinable_with_all": false,
        "combinable_with_levels": ["state", "discom"],
        "mutually_exclusive_with_levels": []
    }
"""

from itertools import combinations

from app.models.enums import IncentiveLevel
from app.schemas.incentive import IncentiveEligibilityResult, IncentiveProgramInput

COMBINATION_REQUIRES_VERIFICATION = "combination_requires_verification"
MUTUALLY_EXCLUSIVE = "mutually_exclusive_with_other_programme"


def apply_stacking_rules(
    evaluated: list[tuple[IncentiveProgramInput, IncentiveEligibilityResult]],
) -> list[IncentiveEligibilityResult]:
    eligible_pairs = [(program, result) for program, result in evaluated if result.eligible]

    for (program_a, result_a), (program_b, result_b) in combinations(eligible_pairs, 2):
        if _either_excludes(program_a, program_b):
            _flag(result_a, MUTUALLY_EXCLUSIVE)
            _flag(result_b, MUTUALLY_EXCLUSIVE)
        elif not _both_confirm_combinable(program_a, program_b):
            _flag(result_a, COMBINATION_REQUIRES_VERIFICATION)
            _flag(result_b, COMBINATION_REQUIRES_VERIFICATION)

    return [result for _, result in evaluated]


def _flag(result: IncentiveEligibilityResult, note: str) -> None:
    # Mutual exclusivity is the stronger signal — never overwrite it with
    # the weaker "requires verification" note.
    if result.combination_note != MUTUALLY_EXCLUSIVE:
        result.combination_note = note


def _either_excludes(program_a: IncentiveProgramInput, program_b: IncentiveProgramInput) -> bool:
    return _lists_level(program_a.stacking_rules, "mutually_exclusive_with_levels", program_b.level) or _lists_level(
        program_b.stacking_rules, "mutually_exclusive_with_levels", program_a.level
    )


def _both_confirm_combinable(program_a: IncentiveProgramInput, program_b: IncentiveProgramInput) -> bool:
    return _allows_combination(program_a.stacking_rules, program_b.level) and _allows_combination(
        program_b.stacking_rules, program_a.level
    )


def _allows_combination(stacking_rules: dict | None, other_level: IncentiveLevel) -> bool:
    if not stacking_rules:
        return False
    if stacking_rules.get("combinable_with_all") is True:
        return True
    return _lists_level(stacking_rules, "combinable_with_levels", other_level)


def _lists_level(stacking_rules: dict | None, key: str, level: IncentiveLevel) -> bool:
    if not stacking_rules:
        return False
    return level.value in (stacking_rules.get(key) or [])
