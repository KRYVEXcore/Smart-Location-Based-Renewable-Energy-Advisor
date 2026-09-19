"""Versioned constants for the Recommendation Engine (Phase 10)."""

RECOMMENDATION_VERSION = "recommendation-2026.1"

# Share of annual consumption a system must generate to count as "reaching the target".
# The single place this number lives; change it here and the rule, the reason text and
# the API response all follow.
TARGET_ANNUAL_COVERAGE_PERCENT = 100.0

# The rule hierarchy, in order. Returned with every result so a recommendation can be audited.
RULES = [
    "1. Options that are technically infeasible or lack the data to be checked (for example an unknown roof area) are excluded.",
    "2. Options screened as insufficient resource are excluded; wind is only considered when its screening is technically feasible.",
    "3. Solar: choose the smallest technically feasible evaluated capacity whose annual coverage reaches the target.",
    "4. If no feasible solar capacity reaches the target, choose the largest technically feasible one and say the target is not met.",
    "5. Solar is preferred over small wind when both are feasible; wind is recommended only when no solar capacity is feasible.",
    "6. Hybrid and battery storage are not recommended: no deterministic engine exists for them yet.",
    "7. Cost, savings and payback are never produced: no verified cost data exists.",
]

COST_UNAVAILABLE_NOTE = "Verified system cost is not currently available, so savings and payback are not calculated."
BUDGET_UNAVAILABLE_NOTE = (
    "A budget was provided, but verified system cost data is not available, so affordability cannot yet be calculated."
)

# When nothing is recommended the advisor still gets an incentive answer for this system,
# the same default the dashboard uses. It is context, not a recommendation.
DEFAULT_INCENTIVE_TECHNOLOGY = "solar"
DEFAULT_INCENTIVE_CAPACITY_KW = 3
