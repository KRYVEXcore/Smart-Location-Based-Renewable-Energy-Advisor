from datetime import date
from decimal import Decimal

from app.engines.tariff.version_selection import select_applicable_version_rows
from app.schemas.tariff import TariffSlabInput

BASE = dict(
    tariff_name="TEST Tariff",
    slab_min_kwh=Decimal("0"),
    slab_max_kwh=None,
    energy_charge_inr_per_kwh=Decimal("5.00"),
)


def row(version: str, effective_from: str, effective_to: str | None = None) -> TariffSlabInput:
    return TariffSlabInput(
        **BASE, tariff_version=version, effective_from=effective_from, effective_to=effective_to
    )


def test_no_version_covers_the_date_returns_empty():
    rows = [row("V1", "2027-01-01")]
    assert select_applicable_version_rows(rows, date(2026, 6, 1)) == []


def test_single_covering_version_is_selected():
    rows = [row("V1", "2026-01-01")]
    result = select_applicable_version_rows(rows, date(2026, 6, 1))
    assert {r.tariff_version for r in result} == {"V1"}


def test_expired_version_is_excluded():
    rows = [row("OLD", "2020-01-01", "2021-12-31")]
    assert select_applicable_version_rows(rows, date(2026, 1, 1)) == []


def test_open_ended_effective_to_still_matches_far_future_date():
    rows = [row("OPEN", "2020-01-01", None)]
    result = select_applicable_version_rows(rows, date(2030, 1, 1))
    assert {r.tariff_version for r in result} == {"OPEN"}


def test_future_version_not_yet_effective_is_excluded():
    rows = [row("FUTURE", "2027-01-01")]
    assert select_applicable_version_rows(rows, date(2026, 1, 1)) == []


def test_picks_the_version_with_the_latest_effective_from_when_two_overlap():
    rows = [
        row("OLD", "2025-01-01", "2027-12-31"),
        row("NEW", "2026-06-01", None),
    ]
    result = select_applicable_version_rows(rows, date(2026, 9, 1))
    assert {r.tariff_version for r in result} == {"NEW"}


def test_tie_break_on_identical_effective_from_is_deterministic_by_version_string():
    rows = [
        row("TN-DOMESTIC-2026.1", "2026-01-01"),
        row("TN-DOMESTIC-2026.2", "2026-01-01"),
    ]
    first_call = select_applicable_version_rows(rows, date(2026, 6, 1))
    second_call = select_applicable_version_rows(list(reversed(rows)), date(2026, 6, 1))

    assert {r.tariff_version for r in first_call} == {"TN-DOMESTIC-2026.2"}
    assert {r.tariff_version for r in first_call} == {r.tariff_version for r in second_call}


def test_only_returns_rows_belonging_to_the_selected_version():
    rows = [
        row("OLD", "2025-01-01", "2025-12-31"),
        row("NEW", "2026-01-01"),
        row("NEW", "2026-01-01"),
    ]
    result = select_applicable_version_rows(rows, date(2026, 6, 1))
    assert len(result) == 2
    assert all(r.tariff_version == "NEW" for r in result)
