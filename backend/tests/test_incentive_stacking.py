import uuid
from datetime import date
from decimal import Decimal

from app.engines.incentive.stacking import MUTUALLY_EXCLUSIVE, COMBINATION_REQUIRES_VERIFICATION, apply_stacking_rules
from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)
from app.schemas.incentive import IncentiveEligibilityResult, IncentiveProgramInput

BASE = dict(
    id=uuid.uuid4(),
    scheme_name="TEST FIXTURE ONLY",
    scheme_version="TEST-V1",
    incentive_type=IncentiveType.CAPITAL_SUBSIDY,
    technology=RenewableTechnology.SOLAR,
    consumer_category=TariffConsumerCategory.RESIDENTIAL,
    subsidy_type=SubsidyType.FIXED_AMOUNT,
    subsidy_value=Decimal("10000"),
    effective_from=date(2026, 1, 1),
    verification_status=IncentiveVerificationStatus.VERIFIED,
    active=True,
)


def program(level, stacking_rules=None, **overrides) -> IncentiveProgramInput:
    data = {**BASE, "level": level, "stacking_rules": stacking_rules}
    data.update(overrides)
    return IncentiveProgramInput(**data)


def eligible_result(scheme_name: str, level: IncentiveLevel) -> IncentiveEligibilityResult:
    return IncentiveEligibilityResult(
        scheme_name=scheme_name,
        level=level,
        technology=RenewableTechnology.SOLAR,
        status="eligible",
        eligible=True,
        incentive_amount_inr="10000.00",
    )


def test_single_eligible_programme_has_no_combination_note():
    central = program(IncentiveLevel.CENTRAL)
    result = eligible_result("A", IncentiveLevel.CENTRAL)
    updated = apply_stacking_rules([(central, result)])
    assert updated[0].combination_note is None


def test_two_eligible_programmes_with_no_documented_rules_require_verification():
    central = program(IncentiveLevel.CENTRAL, stacking_rules=None)
    state = program(IncentiveLevel.STATE, stacking_rules=None)
    updated = apply_stacking_rules(
        [(central, eligible_result("A", IncentiveLevel.CENTRAL)), (state, eligible_result("B", IncentiveLevel.STATE))]
    )
    assert all(r.combination_note == COMBINATION_REQUIRES_VERIFICATION for r in updated)


def test_two_eligible_programmes_both_confirming_combinability_are_not_flagged():
    central = program(IncentiveLevel.CENTRAL, stacking_rules={"combinable_with_levels": ["state"]})
    state = program(IncentiveLevel.STATE, stacking_rules={"combinable_with_levels": ["central"]})
    updated = apply_stacking_rules(
        [(central, eligible_result("A", IncentiveLevel.CENTRAL)), (state, eligible_result("B", IncentiveLevel.STATE))]
    )
    assert all(r.combination_note is None for r in updated)


def test_one_sided_combinability_claim_still_requires_verification():
    # Only the central scheme claims combinability; the state scheme is
    # silent — official rules must establish this from BOTH sides.
    central = program(IncentiveLevel.CENTRAL, stacking_rules={"combinable_with_levels": ["state"]})
    state = program(IncentiveLevel.STATE, stacking_rules=None)
    updated = apply_stacking_rules(
        [(central, eligible_result("A", IncentiveLevel.CENTRAL)), (state, eligible_result("B", IncentiveLevel.STATE))]
    )
    assert all(r.combination_note == COMBINATION_REQUIRES_VERIFICATION for r in updated)


def test_explicitly_mutually_exclusive_programmes_are_flagged():
    central = program(IncentiveLevel.CENTRAL, stacking_rules={"mutually_exclusive_with_levels": ["state"]})
    state = program(IncentiveLevel.STATE, stacking_rules=None)
    updated = apply_stacking_rules(
        [(central, eligible_result("A", IncentiveLevel.CENTRAL)), (state, eligible_result("B", IncentiveLevel.STATE))]
    )
    assert all(r.combination_note == MUTUALLY_EXCLUSIVE for r in updated)


def test_combinable_with_all_flag_allows_combination():
    central = program(IncentiveLevel.CENTRAL, stacking_rules={"combinable_with_all": True})
    state = program(IncentiveLevel.STATE, stacking_rules={"combinable_with_all": True})
    updated = apply_stacking_rules(
        [(central, eligible_result("A", IncentiveLevel.CENTRAL)), (state, eligible_result("B", IncentiveLevel.STATE))]
    )
    assert all(r.combination_note is None for r in updated)


def test_ineligible_programmes_are_never_considered_for_stacking():
    central = program(IncentiveLevel.CENTRAL)
    not_eligible = IncentiveEligibilityResult(
        scheme_name="A", level=IncentiveLevel.CENTRAL, technology=RenewableTechnology.SOLAR,
        status="not_eligible", eligible=False,
    )
    state = program(IncentiveLevel.STATE)
    eligible_state = eligible_result("B", IncentiveLevel.STATE)
    updated = apply_stacking_rules([(central, not_eligible), (state, eligible_state)])
    assert updated[0].combination_note is None
    assert updated[1].combination_note is None
