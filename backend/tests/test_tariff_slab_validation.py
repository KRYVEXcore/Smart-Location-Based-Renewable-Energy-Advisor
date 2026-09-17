from decimal import Decimal

import pytest

from app.engines.tariff.validation import validate_slabs
from app.schemas.tariff import TariffSlabInput

BASE = dict(
    tariff_version="TEST-V1",
    tariff_name="TEST Tariff",
    energy_charge_inr_per_kwh=Decimal("5.00"),
    effective_from="2026-01-01",
)


def slab(min_kwh, max_kwh=None, **overrides) -> TariffSlabInput:
    data = {**BASE, "slab_min_kwh": Decimal(str(min_kwh)), "slab_max_kwh": None if max_kwh is None else Decimal(str(max_kwh))}
    data.update(overrides)
    return TariffSlabInput(**data)


def test_rejects_empty_slab_list():
    with pytest.raises(ValueError, match="At least one"):
        validate_slabs([])


def test_accepts_single_unlimited_slab():
    validate_slabs([slab(0, None)])


def test_accepts_two_contiguous_slabs():
    validate_slabs([slab(0, 100), slab(100, None)])


def test_rejects_negative_slab_minimum():
    with pytest.raises(ValueError, match="negative"):
        validate_slabs([slab(-10, 100), slab(100, None)])


def test_rejects_slab_max_not_greater_than_min():
    with pytest.raises(ValueError, match="greater than"):
        validate_slabs([slab(100, 100)])


def test_rejects_slab_max_less_than_min():
    with pytest.raises(ValueError, match="greater than"):
        validate_slabs([slab(100, 50)])


def test_rejects_first_slab_not_starting_at_zero():
    with pytest.raises(ValueError, match="start at 0"):
        validate_slabs([slab(50, None)])


def test_rejects_gap_between_slabs():
    with pytest.raises(ValueError, match="contiguous"):
        validate_slabs([slab(0, 100), slab(150, None)])


def test_rejects_overlapping_slabs():
    with pytest.raises(ValueError, match="contiguous"):
        validate_slabs([slab(0, 100), slab(50, None)])


def test_rejects_duplicate_slab_minimum():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_slabs([slab(0, 100), slab(0, 200)])


def test_rejects_more_than_one_unlimited_slab():
    with pytest.raises(ValueError, match="final"):
        validate_slabs([slab(0, None), slab(100, None)])


def test_rejects_non_final_slab_with_unlimited_maximum():
    with pytest.raises(ValueError, match="final"):
        validate_slabs([slab(0, None), slab(100, 200)])
