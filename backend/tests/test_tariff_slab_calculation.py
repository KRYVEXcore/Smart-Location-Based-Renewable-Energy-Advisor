from decimal import Decimal

import pytest

from app.engines.tariff.slab_calculation import calculate_slab_energy_charge
from app.schemas.tariff import TariffSlabInput

BASE = dict(tariff_version="TEST-V1", tariff_name="TEST Tariff", effective_from="2026-01-01")

TWO_SLABS = [
    TariffSlabInput(
        **BASE, slab_min_kwh=Decimal("0"), slab_max_kwh=Decimal("100"), energy_charge_inr_per_kwh=Decimal("3.00")
    ),
    TariffSlabInput(
        **BASE, slab_min_kwh=Decimal("100"), slab_max_kwh=None, energy_charge_inr_per_kwh=Decimal("5.00")
    ),
]

THREE_SLABS = [
    TariffSlabInput(
        **BASE, slab_min_kwh=Decimal("0"), slab_max_kwh=Decimal("100"), energy_charge_inr_per_kwh=Decimal("2.50")
    ),
    TariffSlabInput(
        **BASE, slab_min_kwh=Decimal("100"), slab_max_kwh=Decimal("300"), energy_charge_inr_per_kwh=Decimal("4.25")
    ),
    TariffSlabInput(
        **BASE, slab_min_kwh=Decimal("300"), slab_max_kwh=None, energy_charge_inr_per_kwh=Decimal("6.75")
    ),
]


def test_zero_consumption_charges_nothing():
    assert calculate_slab_energy_charge(Decimal("0"), TWO_SLABS) == Decimal("0.00")


def test_negative_consumption_charges_nothing():
    assert calculate_slab_energy_charge(Decimal("-50"), TWO_SLABS) == Decimal("0.00")


def test_consumption_entirely_within_first_slab():
    # 50 kWh entirely at the first slab's rate.
    assert calculate_slab_energy_charge(Decimal("50"), TWO_SLABS) == Decimal("150.00")


def test_consumption_exactly_at_boundary_billed_entirely_in_lower_slab():
    # Exactly 100 kWh: all 100 units at the first (0-100) slab's rate, none
    # spills into the second slab.
    assert calculate_slab_energy_charge(Decimal("100"), TWO_SLABS) == Decimal("300.00")


def test_consumption_just_above_boundary_spills_into_next_slab():
    # 100 units @ 3.00 + 1 unit @ 5.00
    assert calculate_slab_energy_charge(Decimal("101"), TWO_SLABS) == Decimal("305.00")


def test_consumption_spanning_three_slabs():
    # 100 @ 2.50 = 250.00; 200 @ 4.25 = 850.00; 150 @ 6.75 = 1012.50 => 2112.50
    assert calculate_slab_energy_charge(Decimal("450"), THREE_SLABS) == Decimal("2112.50")


def test_consumption_far_into_unlimited_final_slab():
    # 100 @ 2.50 + 200 @ 4.25 + 1000 @ 6.75
    result = calculate_slab_energy_charge(Decimal("1300"), THREE_SLABS)
    assert result == Decimal("250.00") + Decimal("850.00") + Decimal("6750.00")


def test_single_unlimited_slab_charges_flat_rate():
    single = [
        TariffSlabInput(**BASE, slab_min_kwh=Decimal("0"), slab_max_kwh=None, energy_charge_inr_per_kwh=Decimal("6.00"))
    ]
    assert calculate_slab_energy_charge(Decimal("237"), single) == Decimal("1422.00")


def test_decimal_precision_is_exact_not_binary_float_approximate():
    # 0.1 + 0.2 famously != 0.3 in binary float; Decimal must get this exact.
    precise_slabs = [
        TariffSlabInput(
            **BASE, slab_min_kwh=Decimal("0"), slab_max_kwh=None, energy_charge_inr_per_kwh=Decimal("0.1234")
        )
    ]
    result = calculate_slab_energy_charge(Decimal("100"), precise_slabs)
    assert result == Decimal("12.34")


def test_rounding_is_half_up_to_two_decimal_places():
    precise_slabs = [
        TariffSlabInput(
            **BASE, slab_min_kwh=Decimal("0"), slab_max_kwh=None, energy_charge_inr_per_kwh=Decimal("3.005")
        )
    ]
    # 1 kWh * 3.005 = 3.005 -> rounds half-up to 3.01 (not 3.00).
    assert calculate_slab_energy_charge(Decimal("1"), precise_slabs) == Decimal("3.01")


def test_invalid_slabs_raise_instead_of_computing_a_wrong_number():
    overlapping = [
        TariffSlabInput(
            **BASE, slab_min_kwh=Decimal("0"), slab_max_kwh=Decimal("100"), energy_charge_inr_per_kwh=Decimal("3.00")
        ),
        TariffSlabInput(
            **BASE, slab_min_kwh=Decimal("50"), slab_max_kwh=None, energy_charge_inr_per_kwh=Decimal("5.00")
        ),
    ]
    with pytest.raises(ValueError):
        calculate_slab_energy_charge(Decimal("200"), overlapping)
