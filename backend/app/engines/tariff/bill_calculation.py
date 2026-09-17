"""Combines the energy-charge slab calculation with the other tariff charge
components into a single, honestly-labeled breakdown.

Demand and time-of-day charges are always reported "not_calculated": this
app does not collect sanctioned load/kVA or interval consumption data, so
computing them would require guessing an input the assessment never asked
for. Fixed and wheeling charges are "included" only when the tariff data
itself configures a value, and "not_included" otherwise — never
substituted with zero as if that were a real absence of the charge.
"""

from decimal import Decimal

from app.engines.tariff.slab_calculation import TWO_PLACES, calculate_slab_energy_charge
from app.schemas.tariff import TariffChargeComponent, TariffSlabInput


def calculate_charge_components(
    consumption_kwh: Decimal, slabs: list[TariffSlabInput]
) -> list[TariffChargeComponent]:
    components = [
        TariffChargeComponent(
            component="energy",
            status="included",
            amount_inr=str(calculate_slab_energy_charge(consumption_kwh, slabs)),
        )
    ]
    components.append(_fixed_charge_component(slabs))
    components.append(_wheeling_charge_component(consumption_kwh, slabs))
    components.append(
        TariffChargeComponent(
            component="demand",
            status="not_calculated",
            notes=(
                "Demand charges are based on sanctioned load/kVA, which this "
                "assessment does not currently collect."
            ),
        )
    )
    components.append(
        TariffChargeComponent(
            component="tod",
            status="not_calculated",
            notes=(
                "Time-of-day charges require interval (time-of-use) consumption "
                "data, which this assessment does not currently collect."
            ),
        )
    )
    return components


def _fixed_charge_component(slabs: list[TariffSlabInput]) -> TariffChargeComponent:
    fixed_values = {slab.fixed_charge_inr for slab in slabs if slab.fixed_charge_inr is not None}
    if not fixed_values:
        return TariffChargeComponent(
            component="fixed",
            status="not_included",
            notes="No fixed/service charge is configured for this tariff.",
        )
    # All slabs of one tariff_version are expected to share the same fixed
    # charge; sorted() keeps the choice deterministic even if they disagree.
    return TariffChargeComponent(component="fixed", status="included", amount_inr=str(sorted(fixed_values)[0]))


def _wheeling_charge_component(consumption_kwh: Decimal, slabs: list[TariffSlabInput]) -> TariffChargeComponent:
    wheeling_rates = {
        slab.wheeling_charge_inr_per_kwh for slab in slabs if slab.wheeling_charge_inr_per_kwh is not None
    }
    if not wheeling_rates:
        return TariffChargeComponent(
            component="wheeling",
            status="not_included",
            notes="No wheeling charge is configured for this tariff.",
        )
    wheeling_rate = sorted(wheeling_rates)[0]
    amount = (max(consumption_kwh, Decimal("0")) * wheeling_rate).quantize(TWO_PLACES)
    return TariffChargeComponent(component="wheeling", status="included", amount_inr=str(amount))


def sum_included_charges(components: list[TariffChargeComponent]) -> Decimal:
    total = Decimal("0.00")
    for component in components:
        if component.status == "included" and component.amount_inr is not None:
            total += Decimal(component.amount_inr)
    return total.quantize(TWO_PLACES)
