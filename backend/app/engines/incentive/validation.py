"""Structural validation for SLAB_BASED calculation_rules.

Guards against bad seed data (e.g. a typo'd capacity boundary), not user
input — a violation here means the scheme's calculation_rules are
inconsistent and must not be used to compute an amount silently. Mirrors
app.engines.tariff.validation's slab rules, applied to capacity (kW)
instead of consumption (kWh).
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CapacitySlab:
    capacity_min_kw: Decimal
    capacity_max_kw: Decimal | None
    rate_inr_per_kw: Decimal


def validate_capacity_slabs(slabs: list[CapacitySlab]) -> None:
    if not slabs:
        raise ValueError("At least one capacity slab is required for a slab_based scheme.")

    ordered = sorted(slabs, key=lambda slab: slab.capacity_min_kw)

    seen_mins: set[Decimal] = set()
    for slab in ordered:
        if slab.capacity_min_kw < 0:
            raise ValueError(f"Slab minimum cannot be negative: {slab.capacity_min_kw}.")
        if slab.capacity_max_kw is not None and slab.capacity_max_kw <= slab.capacity_min_kw:
            raise ValueError(
                f"Slab maximum ({slab.capacity_max_kw}) must be greater than its minimum "
                f"({slab.capacity_min_kw})."
            )
        if slab.capacity_min_kw in seen_mins:
            raise ValueError(f"Duplicate slab minimum detected: {slab.capacity_min_kw}.")
        seen_mins.add(slab.capacity_min_kw)

    if ordered[0].capacity_min_kw != Decimal("0"):
        raise ValueError(f"The first slab must start at 0 kW, got {ordered[0].capacity_min_kw}.")

    for previous, current in zip(ordered, ordered[1:]):
        if previous.capacity_max_kw is None:
            raise ValueError(
                "Only the final (highest) slab may have an unlimited maximum, but a slab "
                f"starting at {previous.capacity_min_kw} has no maximum and is not the last slab."
            )
        if previous.capacity_max_kw != current.capacity_min_kw:
            raise ValueError(
                "Capacity slabs must be contiguous with no gap or overlap: a slab ending at "
                f"{previous.capacity_max_kw} is followed by a slab starting at {current.capacity_min_kw}."
            )
