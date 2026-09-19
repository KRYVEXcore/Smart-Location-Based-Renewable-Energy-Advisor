"""Loads the DISCOM registry from backend/app/data/discoms/india/ into the
discoms table.

The registry drives DISCOM resolution: a state with exactly one DISCOM
resolves as "identified", a state with several resolves as "ambiguous"
(never guessed). Each DISCOM must cite an official source. Idempotent;
never deletes a row.

Run from backend/ with:

    python -m scripts.seed_discoms [--dry-run] [--expect-database NAME]
"""

import argparse

from sqlalchemy.orm import Session

from app.data_validation import dataset
from app.data_validation.records import DiscomRecord
from app.database.connection import SessionLocal
from app.models.discom import Discom
from scripts._seed_common import (
    SeedStats,
    add_common_arguments,
    assert_expected_database,
    describe_database,
    lock_for_seeding,
    sync_attributes,
)


def load_discom(session: Session, record: DiscomRecord) -> SeedStats:
    stats = SeedStats()
    query = session.query(Discom).filter(Discom.short_code == record.short_code)
    query = query.filter(Discom.state == record.state) if record.state else query.filter(
        Discom.union_territory == record.union_territory
    )
    existing = query.one_or_none()

    desired = {
        "name": record.name,
        "short_code": record.short_code,
        "state": record.state,
        "union_territory": record.union_territory,
        "is_active": record.is_active,
    }
    if existing is None:
        session.add(Discom(**desired))
        stats.inserted += 1
    elif sync_attributes(existing, desired, numeric=set()):
        stats.updated += 1
    else:
        stats.unchanged += 1
    return stats


def seed_all(
    *, dry_run: bool = False, expect_database: str | None = None, session: Session | None = None
) -> SeedStats:
    """With `session` given (see scripts.seed_all) the caller owns commit/rollback,
    so several steps can share one transaction.
    """
    loaded = dataset.load_discom_records()
    problems = dataset.check_discom_dataset(loaded)
    if problems:
        raise SystemExit("DISCOM data failed validation:\n  " + "\n  ".join(problems))

    owns_session = session is None
    session = session or SessionLocal()
    total = SeedStats()
    try:
        assert_expected_database(session, expect_database)
        lock_for_seeding(session)
        print(f"[discoms] target: {describe_database(session)}")
        before = session.query(Discom).count()
        for _, record in loaded:
            total.add(load_discom(session, record))
            session.flush()
        after = session.query(Discom).count()
        if owns_session:
            session.rollback() if dry_run else session.commit()
        print(f"[discoms] rows before={before} after={after if not (dry_run and owns_session) else before} | {total.summary()}"
              f"{' (dry run, nothing written)' if dry_run else ''}")
    except Exception:
        if owns_session:
            session.rollback()
        raise
    finally:
        if owns_session:
            session.close()
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_common_arguments(parser)
    args = parser.parse_args()
    seed_all(dry_run=args.dry_run, expect_database=args.expect_database)
