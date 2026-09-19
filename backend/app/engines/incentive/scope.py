"""Regional applicability of a single incentive programme row.

The repository returns every CENTRAL programme for any location, but a
central scheme can pay a different rate in certain states/UTs (PM Surya
Ghar's "special category" States/UTs). Those variants are separate rows
with the same scheme name, so exactly one variant must apply to a given
location — never both, never by row order.

A row applies to a location when ALL of these hold:
  - its own `state` / `union_territory`, if set, equals the location's;
  - `eligibility_rules["applies_only_to_states"]` /
    `["applies_only_to_union_territories"]`, if present, include the
    location's state/UT;
  - `eligibility_rules["excluded_states"]` / `["excluded_union_territories"]`,
    if present, do not include the location's state/UT.

A location with no resolved state/UT never matches a row that is scoped or
restricted to a region: this never guesses that it "probably" is.
"""

from typing import Protocol


class RegionScopedProgram(Protocol):
    state: str | None
    union_territory: str | None
    eligibility_rules: dict | None


def applies_to_region(
    program: RegionScopedProgram, *, state: str | None, union_territory: str | None
) -> bool:
    if program.state is not None and program.state != state:
        return False
    if program.union_territory is not None and program.union_territory != union_territory:
        return False

    rules = program.eligibility_rules or {}

    only_states = rules.get("applies_only_to_states")
    only_uts = rules.get("applies_only_to_union_territories")
    if only_states is not None or only_uts is not None:
        in_states = state is not None and state in (only_states or [])
        in_uts = union_territory is not None and union_territory in (only_uts or [])
        if not (in_states or in_uts):
            return False

    if state is not None and state in (rules.get("excluded_states") or []):
        return False
    if union_territory is not None and union_territory in (rules.get("excluded_union_territories") or []):
        return False

    return True
