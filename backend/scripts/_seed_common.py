"""Shared helpers for the seed scripts.

None of the seed scripts deletes a row. Each one upserts by a natural key
so running it twice is a no-op, and a row that is no longer in the data
files is deactivated rather than removed.
"""

import argparse
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class SeedStats:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    deactivated: int = 0
    rejected: list[str] = field(default_factory=list)

    def add(self, other: "SeedStats") -> None:
        self.inserted += other.inserted
        self.updated += other.updated
        self.unchanged += other.unchanged
        self.deactivated += other.deactivated
        self.rejected.extend(other.rejected)

    def summary(self) -> str:
        return (
            f"inserted={self.inserted} updated={self.updated} unchanged={self.unchanged} "
            f"deactivated={self.deactivated} rejected={len(self.rejected)}"
        )


def same_number(a: object, b: object) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return Decimal(str(a)) == Decimal(str(b))


def sync_attributes(row: object, desired: dict[str, object], numeric: set[str]) -> bool:
    """Sets each attribute on `row` that differs from `desired`; returns
    whether anything changed.
    """
    changed = False
    for name, value in desired.items():
        current = getattr(row, name)
        equal = same_number(current, value) if name in numeric else current == value
        if not equal:
            setattr(row, name, value)
            changed = True
    return changed


def describe_database(session: Session) -> str:
    """host:port/database (password hidden) and the applied Alembic revision,
    so the operator can confirm which database is about to be written.
    """
    url = session.get_bind().url
    try:
        revision = session.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception:
        session.rollback()
        revision = "unknown (no alembic_version table)"
    return f"{url.host or 'local'}:{url.port or ''}/{url.database} [{url.drivername}] alembic={revision}"


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="Validate and report; write nothing.")
    parser.add_argument(
        "--expect-database",
        metavar="NAME",
        help="Abort unless the connected database has exactly this name.",
    )


def assert_expected_database(session: Session, expected: str | None) -> None:
    if expected is None:
        return
    actual = session.get_bind().url.database
    if actual != expected:
        raise SystemExit(f"Refusing to seed: connected to database {actual!r}, expected {expected!r}.")
