"""Combines the energy-charge slab calculation with the other tariff charge
components into a single, honestly-labeled breakdown.

Demand and time-of-day charges are always reported "not_calculated": this
app does not collect sanctioned load/kVA or interval consumption data, so
computing them would require guessing an input the assessment never asked
for. Wheeling charges are "included" only when the tariff data itself
configures a value, and "not_included" otherwise — never substituted with
zero as if that were a real absence of the charge.

Fixed charges depend on what they are charged *per* (see FixedChargeBasis):
a flat monthly/per-connection amount is included; a per-kW/kVA/HP amount is
"not_calculated" because sanctioned load is not collected; and a fixed
charge with no recorded basis is never assumed to be monthly.
"""

from decimal import Decimal

from app.models.enums import FixedChargeBasis

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
    components.append(_fixed_charge_component(consumption_kwh, slabs))
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


_FLAT_MONTHLY_BASES = {FixedChargeBasis.INR_PER_MONTH, FixedChargeBasis.INR_PER_CONNECTION_PER_MONTH}


def _slab_containing(consumption_kwh: Decimal, slabs: list[TariffSlabInput]) -> TariffSlabInput:
    """The slab the *total* consumption falls in — the same boundary rule as
    calculate_slab_energy_charge: consumption exactly on a boundary belongs
    to the lower slab. Some tariffs (e.g. Rajasthan, Kerala) set the fixed
    charge by the consumption bracket rather than as one flat number.
    """
    ordered = sorted(slabs, key=lambda slab: slab.slab_min_kwh)
    for slab in ordered:
        if slab.slab_max_kwh is None or consumption_kwh <= slab.slab_max_kwh:
            return slab
    return ordered[-1]


def _fixed_charge_component(consumption_kwh: Decimal, slabs: list[TariffSlabInput]) -> TariffChargeComponent:
    slab = _slab_containing(max(consumption_kwh, Decimal("0")), slabs)
    rate = slab.fixed_charge_inr
    if rate is None:
        return TariffChargeComponent(
            component="fixed",
            status="not_included",
            notes="No fixed/service charge is configured for this tariff.",
        )
    if rate == Decimal("0"):
        return TariffChargeComponent(
            component="fixed",
            status="included",
            amount_inr=str(rate.quantize(TWO_PLACES)),
            notes="The tariff order specifies no fixed charge.",
        )
    if slab.fixed_charge_basis in _FLAT_MONTHLY_BASES:
        return TariffChargeComponent(component="fixed", status="included", amount_inr=str(rate.quantize(TWO_PLACES)))
    if slab.fixed_charge_basis is None:
        return TariffChargeComponent(
            component="fixed",
            status="not_calculated",
            notes="A fixed charge is recorded but not what it is charged per, so it is not billed.",
        )
    unit = slab.fixed_charge_basis.value.replace("inr_per_", "").replace("_per_month", "").upper()
    return TariffChargeComponent(
        component="fixed",
        status="not_calculated",
        notes=(
            f"The fixed charge is Rs {rate} per {unit} per month, which depends on the "
            "sanctioned load/demand. This assessment does not collect it."
        ),
    )


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
