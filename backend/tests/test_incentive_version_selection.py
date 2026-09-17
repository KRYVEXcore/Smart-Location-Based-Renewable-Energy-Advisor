import uuid
from datetime import date

from app.engines.incentive.version_selection import group_by_scheme, select_scheme_version
from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)
from app.schemas.incentive import IncentiveProgramInput

BASE = dict(
    scheme_name="TEST FIXTURE ONLY — Scheme",
    level=IncentiveLevel.CENTRAL,
    incentive_type=IncentiveType.CAPITAL_SUBSIDY,
    technology=RenewableTechnology.SOLAR,
    consumer_category=TariffConsumerCategory.RESIDENTIAL,
    subsidy_type=SubsidyType.FIXED_AMOUNT,
    subsidy_value=10000,
    verification_status=IncentiveVerificationStatus.VERIFIED,
    active=True,
)


def row(version: str, effective_from: str, effective_to: str | None = None, **overrides) -> IncentiveProgramInput:
    data = {**BASE, "id": uuid.uuid4(), "scheme_version": version, "effective_from": effective_from, "effective_to": effective_to}
    data.update(overrides)
    return IncentiveProgramInput(**data)


def test_no_version_covers_the_date_and_all_versions_are_future_is_not_active():
    rows = [row("V1", "2027-01-01")]
    result = select_scheme_version(rows, date(2026, 6, 1))
    assert result.status == "scheme_not_active"
    assert result.row is None


def test_no_version_covers_the_date_and_all_versions_are_past_is_expired():
    rows = [row("V1", "2020-01-01", "2021-12-31")]
    result = select_scheme_version(rows, date(2026, 1, 1))
    assert result.status == "scheme_expired"
    assert result.row is None


def test_single_covering_version_is_selected():
    rows = [row("V1", "2026-01-01")]
    result = select_scheme_version(rows, date(2026, 6, 1))
    assert result.status == "ok"
    assert result.row.scheme_version == "V1"


def test_open_ended_effective_to_matches_far_future_date():
    rows = [row("OPEN", "2020-01-01", None)]
    result = select_scheme_version(rows, date(2030, 1, 1))
    assert result.status == "ok"


def test_picks_the_version_with_the_latest_effective_from_when_two_overlap():
    rows = [
        row("OLD", "2024-01-01", "2027-12-31"),
        row("NEW", "2026-06-01", None),
    ]
    result = select_scheme_version(rows, date(2026, 9, 1))
    assert result.row.scheme_version == "NEW"


def test_tie_break_on_identical_effective_from_is_deterministic_by_version_string():
    rows = [
        row("PMSG-2026.1", "2026-01-01"),
        row("PMSG-2026.2", "2026-01-01"),
    ]
    first = select_scheme_version(rows, date(2026, 6, 1))
    second = select_scheme_version(list(reversed(rows)), date(2026, 6, 1))
    assert first.row.scheme_version == "PMSG-2026.2"
    assert first.row.scheme_version == second.row.scheme_version


def test_group_by_scheme_separates_distinct_schemes():
    rows = [
        row("V1", "2026-01-01", scheme_name="Scheme A"),
        row("V1", "2026-01-01", scheme_name="Scheme B"),
        row("V1", "2026-01-01", scheme_name="Scheme A", level=IncentiveLevel.STATE),
    ]
    grouped = group_by_scheme(rows)
    assert len(grouped) == 3


def test_group_by_scheme_keeps_versions_of_the_same_scheme_together():
    rows = [
        row("V1", "2024-01-01", "2025-12-31"),
        row("V2", "2026-01-01"),
    ]
    grouped = group_by_scheme(rows)
    assert len(grouped) == 1
    ((key, scheme_rows),) = grouped.items()
    assert len(scheme_rows) == 2
