"""Structural validation for a set of tariff slabs.

This guards against bad seed/source data (e.g. a typo'd slab boundary), not
against user input — a violation here means the tariff dataset itself is
inconsistent and must not be used to compute a bill silently. Every check
raises ValueError with a specific reason; nothing here guesses a fix.
"""

from decimal import Decimal

from app.schemas.tariff import TariffSlabInput


def validate_slabs(slabs: list[TariffSlabInput]) -> None:
    if not slabs:
        raise ValueError("At least one tariff slab is required.")

    ordered = sorted(slabs, key=lambda slab: slab.slab_min_kwh)

    seen_mins: set[Decimal] = set()
    for slab in ordered:
        if slab.slab_min_kwh < 0:
            raise ValueError(f"Slab minimum cannot be negative: {slab.slab_min_kwh}.")
        if slab.slab_max_kwh is not None and slab.slab_max_kwh <= slab.slab_min_kwh:
            raise ValueError(
                f"Slab maximum ({slab.slab_max_kwh}) must be greater than its minimum "
                f"({slab.slab_min_kwh})."
            )
        if slab.slab_min_kwh in seen_mins:
            raise ValueError(f"Duplicate slab minimum detected: {slab.slab_min_kwh}.")
        seen_mins.add(slab.slab_min_kwh)

    if ordered[0].slab_min_kwh != Decimal("0"):
        raise ValueError(f"The first slab must start at 0 kWh, got {ordered[0].slab_min_kwh}.")

    for previous, current in zip(ordered, ordered[1:]):
        if previous.slab_max_kwh is None:
            raise ValueError(
                "Only the final (highest) slab may have an unlimited maximum, but a slab "
                f"starting at {previous.slab_min_kwh} has no maximum and is not the last slab."
            )
        if previous.slab_max_kwh != current.slab_min_kwh:
            raise ValueError(
                "Tariff slabs must be contiguous with no gap or overlap: a slab ending at "
                f"{previous.slab_max_kwh} is followed by a slab starting at {current.slab_min_kwh}."
            )
