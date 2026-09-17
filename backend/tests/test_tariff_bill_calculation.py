from decimal import Decimal

from app.engines.tariff.bill_calculation import calculate_charge_components, sum_included_charges
from app.schemas.tariff import TariffSlabInput

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
    slabs = [TariffSlabInput(**BASE, fixed_charge_inr=Decimal("75.00"))]
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
    slabs = [TariffSlabInput(**BASE, fixed_charge_inr=Decimal("50.00"))]
    components = calculate_charge_components(Decimal("100"), slabs)

    # energy (500.00) + fixed (50.00); wheeling not_included, demand/tod not_calculated.
    assert sum_included_charges(components) == Decimal("550.00")


def test_sum_included_charges_with_all_components_present():
    slabs = [
        TariffSlabInput(
            **BASE, fixed_charge_inr=Decimal("50.00"), wheeling_charge_inr_per_kwh=Decimal("0.25")
        )
    ]
    components = calculate_charge_components(Decimal("100"), slabs)

    # energy 500.00 + fixed 50.00 + wheeling 25.00 = 575.00
    assert sum_included_charges(components) == Decimal("575.00")
