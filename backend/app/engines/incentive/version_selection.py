"""Deterministic incentive scheme-version selection by effective date range.

A distinct scheme (identified by scheme_name + level + technology — see
group_by_scheme) can have several scheme_version rows on file over time
(e.g. PM Surya Ghar v1 in 2024, v2 in 2025, v3 in 2026). Exactly one
version must be chosen for a given calculation_date — never randomly, and
never by database row order. Unlike the Tariff Engine (where a whole
schedule is one group of slab rows), an incentive scheme version is
usually a single row.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.models.enums import IncentiveLevel, RenewableTechnology
from app.schemas.incentive import IncentiveProgramInput

SchemeKey = tuple[str, IncentiveLevel, RenewableTechnology]


@dataclass(frozen=True)
class VersionSelection:
    """`row` is None unless status == "ok"."""

    status: Literal["ok", "scheme_expired", "scheme_not_active"]
    row: IncentiveProgramInput | None


def group_by_scheme(rows: list[IncentiveProgramInput]) -> dict[SchemeKey, list[IncentiveProgramInput]]:
    """Groups candidate rows into distinct schemes — different versions of
    "the same scheme" share a scheme_name, level, and technology.
    """
    grouped: dict[SchemeKey, list[IncentiveProgramInput]] = {}
    for row in rows:
        grouped.setdefault((row.scheme_name, row.level, row.technology), []).append(row)
    return grouped


def select_scheme_version(scheme_rows: list[IncentiveProgramInput], calculation_date: date) -> VersionSelection:
    """Picks the version whose [effective_from, effective_to] range covers
    calculation_date, preferring the latest effective_from with ties
    broken by the scheme_version string — deterministic regardless of row
    order. If no version covers the date, reports whether every version is
    in the past (scheme_expired) or the future (scheme_not_active) rather
    than silently omitting the scheme.
    """
    candidates = [
        row
        for row in scheme_rows
        if row.effective_from <= calculation_date
        and (row.effective_to is None or calculation_date <= row.effective_to)
    ]

    if not candidates:
        if all(row.effective_from > calculation_date for row in scheme_rows):
            return VersionSelection(status="scheme_not_active", row=None)
        return VersionSelection(status="scheme_expired", row=None)

    by_version: dict[str, list[IncentiveProgramInput]] = {}
    for row in candidates:
        by_version.setdefault(row.scheme_version, []).append(row)

    def version_sort_key(version: str) -> tuple[date, str]:
        earliest_effective_from = min(row.effective_from for row in by_version[version])
        return (earliest_effective_from, version)

    best_version = max(by_version, key=version_sort_key)
    # Multiple rows for one version aren't expected in practice (one row =
    # one scheme version), but pick deterministically if it ever happens.
    return VersionSelection(status="ok", row=sorted(by_version[best_version], key=lambda r: r.id.hex)[0])
