"""Cumulative/progressive (telescoping) slab energy-charge calculation.

All money math uses Decimal — never float — to avoid binary
floating-point rounding error in a billing calculation.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.engines.tariff.validation import validate_slabs
from app.schemas.tariff import TariffSlabInput

TWO_PLACES = Decimal("0.01")


def calculate_slab_energy_charge(consumption_kwh: Decimal, slabs: list[TariffSlabInput]) -> Decimal:
    """Each slab covers [slab_min_kwh, slab_max_kwh) kWh — the final slab's
    slab_max_kwh is None and extends indefinitely. Consumption landing
    exactly on a boundary is billed entirely within the lower slab: with
    slabs [0, 100) and [100, None), 100 kWh of consumption is billed
    entirely at the first slab's rate, and the second slab only applies to
    consumption above 100 kWh.

    Raises ValueError (via validate_slabs) if the slabs themselves are
    inconsistent (overlapping, negative, non-contiguous, or more than one
    unlimited slab) — this never silently guesses a fix for bad data.
    """
    validate_slabs(slabs)

    if consumption_kwh <= Decimal("0"):
        return Decimal("0.00")

    total = Decimal("0")
    for slab in sorted(slabs, key=lambda slab: slab.slab_min_kwh):
        if consumption_kwh <= slab.slab_min_kwh:
            continue
        upper_bound = (
            consumption_kwh if slab.slab_max_kwh is None else min(consumption_kwh, slab.slab_max_kwh)
        )
        units_in_slab = upper_bound - slab.slab_min_kwh
        total += units_in_slab * slab.energy_charge_inr_per_kwh

    return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
