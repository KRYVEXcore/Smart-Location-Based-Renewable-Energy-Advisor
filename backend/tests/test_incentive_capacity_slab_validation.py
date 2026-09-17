from decimal import Decimal

import pytest

from app.engines.incentive.validation import CapacitySlab, validate_capacity_slabs


def slab(min_kw, max_kw=None, rate="30000") -> CapacitySlab:
    return CapacitySlab(
        capacity_min_kw=Decimal(str(min_kw)),
        capacity_max_kw=None if max_kw is None else Decimal(str(max_kw)),
        rate_inr_per_kw=Decimal(rate),
    )


def test_rejects_empty_slab_list():
    with pytest.raises(ValueError, match="At least one"):
        validate_capacity_slabs([])


def test_accepts_single_unlimited_slab():
    validate_capacity_slabs([slab(0, None)])


def test_accepts_two_contiguous_slabs():
    validate_capacity_slabs([slab(0, 2), slab(2, None)])


def test_rejects_negative_slab_minimum():
    with pytest.raises(ValueError, match="negative"):
        validate_capacity_slabs([slab(-1, 2), slab(2, None)])


def test_rejects_slab_max_not_greater_than_min():
    with pytest.raises(ValueError, match="greater than"):
        validate_capacity_slabs([slab(2, 2)])


def test_rejects_first_slab_not_starting_at_zero():
    with pytest.raises(ValueError, match="start at 0"):
        validate_capacity_slabs([slab(1, None)])


def test_rejects_gap_between_slabs():
    with pytest.raises(ValueError, match="contiguous"):
        validate_capacity_slabs([slab(0, 2), slab(3, None)])


def test_rejects_overlapping_slabs():
    with pytest.raises(ValueError, match="contiguous"):
        validate_capacity_slabs([slab(0, 2), slab(1, None)])


def test_rejects_duplicate_slab_minimum():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_capacity_slabs([slab(0, 2), slab(0, 3)])


def test_rejects_non_final_slab_with_unlimited_maximum():
    with pytest.raises(ValueError, match="final"):
        validate_capacity_slabs([slab(0, None), slab(2, 3)])
