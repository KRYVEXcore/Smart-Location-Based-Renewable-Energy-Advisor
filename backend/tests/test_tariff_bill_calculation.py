from decimal import Decimal

from app.engines.tariff.bill_calculation import calculate_charge_components, sum_included_charges
from app.models.enums import FixedChargeBasis
from app.schemas.tariff import TariffSlabInput

MONTHLY = FixedChargeBasis.INR_PER_MONTH

BASE = dict(
    tariff_version="TEST-V1",
    tariff_name="TEST Tariff",
    slab_min_kwh=Decimal("0"),
    slab_max_kwh=None,
    energy_charge_inr_per_kwh=Decimal("5.00"),
    effective_from="2026-01-01",
)


def test_demand_and_tod_are_always_not_calculated():
    slabs = [TariffSlabInput(**BASE)]
    components = calculate_charge_components(Decimal("100"), slabs)

    by_name = {c.component: c for c in components}
    assert by_name["demand"].status == "not_calculated"
    assert by_name["demand"].amount_inr is None
    assert by_name["tod"].status == "not_calculated"
    assert by_name["tod"].amount_inr is None


def test_fixed_charge_included_when_configured():
    slabs = [TariffSlabInput(**BASE, fixed_charge_inr=Decimal("75.00"), fixed_charge_basis=MONTHLY)]
    components = calculate_charge_components(Decimal("100"), slabs)

    fixed = next(c for c in components if c.component == "fixed")
    assert fixed.status == "included"
    assert fixed.amount_inr == "75.00"


def test_fixed_charge_not_included_when_absent():
    slabs = [TariffSlabInput(**BASE)]
    components = calculate_charge_components(Decimal("100"), slabs)

    fixed = next(c for c in components if c.component == "fixed")
    assert fixed.status == "not_included"
    assert fixed.amount_inr is None


def test_wheeling_charge_included_and_computed_from_consumption():
    slabs = [TariffSlabInput(**BASE, wheeling_charge_inr_per_kwh=Decimal("0.50"))]
    components = calculate_charge_components(Decimal("200"), slabs)

    wheeling = next(c for c in components if c.component == "wheeling")
    assert wheeling.status == "included"
    assert wheeling.amount_inr == "100.00"


def test_wheeling_charge_not_included_when_absent():
    slabs = [TariffSlabInput(**BASE)]
    components = calculate_charge_components(Decimal("200"), slabs)

    wheeling = next(c for c in components if c.component == "wheeling")
    assert wheeling.status == "not_included"


def test_energy_component_always_included_and_matches_slab_calculation():
    slabs = [TariffSlabInput(**BASE)]
    components = calculate_charge_components(Decimal("100"), slabs)

    energy = next(c for c in components if c.component == "energy")
    assert energy.status == "included"
    assert energy.amount_inr == "500.00"


def test_sum_included_charges_excludes_not_included_and_not_calculated():
    slabs = [TariffSlabInput(**BASE, fixed_charge_inr=Decimal("50.00"), fixed_charge_basis=MONTHLY)]
    components = calculate_charge_components(Decimal("100"), slabs)

    # energy (500.00) + fixed (50.00); wheeling not_included, demand/tod not_calculated.
    assert sum_included_charges(components) == Decimal("550.00")


def test_sum_included_charges_with_all_components_present():
    slabs = [
        TariffSlabInput(
            **BASE, fixed_charge_inr=Decimal("50.00"), fixed_charge_basis=MONTHLY, wheeling_charge_inr_per_kwh=Decimal("0.25")
        )
    ]
    components = calculate_charge_components(Decimal("100"), slabs)

    # energy 500.00 + fixed 50.00 + wheeling 25.00 = 575.00
    assert sum_included_charges(components) == Decimal("575.00")


def _fixed(components):
    return next(c for c in components if c.component == "fixed")


def test_per_kw_fixed_charge_is_not_calculated_never_a_flat_monthly_amount():
    slabs = [
        TariffSlabInput(
            **BASE, fixed_charge_inr=Decimal("150.00"), fixed_charge_basis=FixedChargeBasis.INR_PER_KW_PER_MONTH
        )
    ]
    components = calculate_charge_components(Decimal("300"), slabs)

    fixed = _fixed(components)
    assert fixed.status == "not_calculated"
    assert fixed.amount_inr is None
    assert "sanctioned load" in fixed.notes
    assert sum_included_charges(components) == Decimal("1500.00")  # energy only


def test_fixed_charge_with_no_recorded_basis_is_never_assumed_monthly():
    slabs = [TariffSlabInput(**BASE, fixed_charge_inr=Decimal("75.00"))]

    fixed = _fixed(calculate_charge_components(Decimal("100"), slabs))

    assert fixed.status == "not_calculated"
    assert fixed.amount_inr is None


def test_nil_fixed_charge_is_reported_as_zero_regardless_of_basis():
    slabs = [
        TariffSlabInput(
            **BASE, fixed_charge_inr=Decimal("0"), fixed_charge_basis=FixedChargeBasis.INR_PER_KW_PER_MONTH
        )
    ]

    fixed = _fixed(calculate_charge_components(Decimal("100"), slabs))

    assert fixed.status == "included"
    assert fixed.amount_inr == "0.00"


def _bracketed_slabs():
    def slab(low, high, fixed):
        return TariffSlabInput(
            **{
                **BASE,
                "slab_min_kwh": Decimal(low),
                "slab_max_kwh": None if high is None else Decimal(high),
            },
            fixed_charge_inr=Decimal(fixed),
            fixed_charge_basis=MONTHLY,
        )

    return [slab("0", "150", "150"), slab("150", "300", "300"), slab("300", None, "500")]


def test_fixed_charge_follows_the_bracket_the_total_consumption_falls_in():
    slabs = _bracketed_slabs()

    assert _fixed(calculate_charge_components(Decimal("100"), slabs)).amount_inr == "150.00"
    assert _fixed(calculate_charge_components(Decimal("220"), slabs)).amount_inr == "300.00"
    assert _fixed(calculate_charge_components(Decimal("950"), slabs)).amount_inr == "500.00"


def test_consumption_exactly_on_a_bracket_boundary_uses_the_lower_bracket():
    slabs = _bracketed_slabs()

    assert _fixed(calculate_charge_components(Decimal("150"), slabs)).amount_inr == "150.00"
    assert _fixed(calculate_charge_components(Decimal("300"), slabs)).amount_inr == "300.00"
