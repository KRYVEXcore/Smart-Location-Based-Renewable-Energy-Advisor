"""Deterministic tariff-version selection by effective date range.

A state/DISCOM/category can have several tariff_version schedules on file
over time (e.g. superseded tariff orders kept for historical reproducibility
of past calculations). Exactly one version must be chosen for a given
calculation_date — never randomly, and never by database row order.
"""

from datetime import date

from app.schemas.tariff import TariffSlabInput


def select_applicable_version_rows(
    rows: list[TariffSlabInput], calculation_date: date
) -> list[TariffSlabInput]:
    """Keeps only rows whose [effective_from, effective_to] range covers
    calculation_date, then picks exactly one tariff_version: the one with
    the latest effective_from. Ties (two versions effective from the same
    date) are broken by the tariff_version string itself, descending, so
    the result is fully deterministic regardless of input row order.

    Returns an empty list if no version covers calculation_date.
    """
    candidates = [
        row
        for row in rows
        if row.effective_from <= calculation_date
        and (row.effective_to is None or calculation_date <= row.effective_to)
    ]
    if not candidates:
        return []

    by_version: dict[str, list[TariffSlabInput]] = {}
    for row in candidates:
        by_version.setdefault(row.tariff_version, []).append(row)

    def version_sort_key(version: str) -> tuple[date, str]:
        earliest_effective_from = min(row.effective_from for row in by_version[version])
        return (earliest_effective_from, version)

    best_version = max(by_version, key=version_sort_key)
    return by_version[best_version]
