"""Runs the DISCOM, tariff and incentive seeds in dependency order, in ONE
transaction: with --dry-run everything is validated and reported and then
rolled back; otherwise it is committed only if every step succeeded.

Each step validates its own data first and is idempotent, so this is safe
to run on every deploy. Run from backend/ with:

    python -m scripts.seed_all [--dry-run] [--expect-database NAME]
"""

import argparse

from app.database.connection import SessionLocal
from scripts import seed_discoms, seed_incentives, seed_tariffs
from scripts._seed_common import add_common_arguments


def run(*, dry_run: bool = False, expect_database: str | None = None) -> None:
    session = SessionLocal()
    try:
        for step in (seed_discoms, seed_tariffs, seed_incentives):
            step.seed_all(dry_run=dry_run, expect_database=expect_database, session=session)
        if dry_run:
            session.rollback()
            print("[seed_all] dry run complete, nothing written")
        else:
            session.commit()
            print("[seed_all] committed")
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_common_arguments(parser)
    args = parser.parse_args()
    run(dry_run=args.dry_run, expect_database=args.expect_database)
