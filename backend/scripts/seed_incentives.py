"""Loads verified incentive programmes from
backend/app/data/incentives/india/ into the incentive_programs table.

Not wired into app startup by default: seeding real government scheme data
is a deliberate, reviewed action. Every file is validated first (official
source, complete provenance, capacity slabs, no overlapping regional
variants) and nothing is written if any file fails.

Idempotent and non-destructive: each scheme version is upserted by its
natural key (scheme_name, level, technology, scheme_version), so running
this twice changes nothing and a historical version is never overwritten by
a newer one. A row is never deleted.

Run from backend/ with:

    python -m scripts.seed_incentives [--dry-run] [--expect-database NAME]
"""

import argparse

from sqlalchemy.orm import Session

from app.data_validation import dataset
from app.data_validation.records import IncentiveRecord
from app.database.connection import SessionLocal
from app.models.discom import Discom
from app.models.incentive_program import IncentiveProgram
from scripts._seed_common import (
    SeedStats,
    add_common_arguments,
    assert_expected_database,
    describe_database,
    sync_attributes,
)

NUMERIC_FIELDS = {
    "min_system_size_kw",
    "max_system_size_kw",
    "subsidy_value",
    "percentage_value",
    "maximum_amount",
}


def resolve_discom_id(session: Session, record: IncentiveRecord):
    if record.discom_short_code is None:
        return None
    query = session.query(Discom).filter(Discom.short_code == record.discom_short_code)
    query = query.filter(Discom.state == record.state) if record.state else query.filter(
        Discom.union_territory == record.union_territory
    )
    discom = query.one_or_none()
    if discom is None:
        raise ValueError(f"No DISCOM found with short_code={record.discom_short_code!r}")
    return discom.id


def load_scheme(session: Session, record: IncentiveRecord) -> SeedStats:
    stats = SeedStats()
    source = record.source
    desired = {
        "description": record.description,
        "incentive_type": record.incentive_type,
        "state": record.state,
        "union_territory": record.union_territory,
        "discom_id": resolve_discom_id(session, record),
        "consumer_category": record.consumer_category,
        "min_system_size_kw": record.min_system_size_kw,
        "max_system_size_kw": record.max_system_size_kw,
        "subsidy_type": record.subsidy_type,
        "subsidy_value": record.subsidy_value,
        "percentage_value": record.percentage_value,
        "maximum_amount": record.maximum_amount,
        "calculation_rules": _jsonable(record.calculation_rules),
        "eligibility_rules": _jsonable(record.eligibility_rules),
        "application_requirements": _jsonable(record.application_requirements),
        "stacking_rules": _jsonable(record.stacking_rules),
        "effective_from": record.effective_from,
        "effective_to": record.effective_to,
        "verification_status": record.verification_status,
        "source_name": source.name,
        "source_url": source.url,
        "source_document": source.document,
        "source_order_number": source.order_number,
        "source_order_date": source.order_date,
        "source_page": source.page,
        "source_table": source.table,
        "source_section": source.section,
        "source_excerpt": source.excerpt,
        "verification_notes": record.verification_notes,
        "last_verified": source.last_verified,
        "active": record.active,
    }

    existing = (
        session.query(IncentiveProgram)
        .filter(
            IncentiveProgram.scheme_name == record.scheme_name,
            IncentiveProgram.level == record.level,
            IncentiveProgram.technology == record.technology,
            IncentiveProgram.scheme_version == record.scheme_version,
        )
        .one_or_none()
    )
    if existing is None:
        session.add(
            IncentiveProgram(
                scheme_name=record.scheme_name,
                scheme_version=record.scheme_version,
                level=record.level,
                technology=record.technology,
                **desired,
            )
        )
        stats.inserted += 1
    elif sync_attributes(existing, desired, NUMERIC_FIELDS):
        stats.updated += 1
    else:
        stats.unchanged += 1
    return stats


def _jsonable(value):
    """JSON columns cannot store Decimal; convert numbers to plain JSON
    numbers via their exact string form (calculate_incentive_amount
    re-parses them with Decimal(str(...)), so no precision is lost).
    """
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "as_tuple"):  # Decimal
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def seed_all(
    *, dry_run: bool = False, expect_database: str | None = None, session: Session | None = None
) -> SeedStats:
    """With `session` given (see scripts.seed_all) the caller owns commit/rollback,
    so several steps can share one transaction.
    """
    incentives = dataset.load_incentive_records()
    problems = dataset.check_incentive_dataset(incentives)
    if problems:
        raise SystemExit("Incentive data failed validation, nothing written:\n  " + "\n  ".join(problems))

    owns_session = session is None
    session = session or SessionLocal()
    total = SeedStats()
    try:
        assert_expected_database(session, expect_database)
        print(f"[incentives] target: {describe_database(session)}")
        before = session.query(IncentiveProgram).count()
        for _, record in incentives:
            total.add(load_scheme(session, record))
            session.flush()
        after = session.query(IncentiveProgram).count()
        if owns_session:
            session.rollback() if dry_run else session.commit()
        print(
            f"[incentives] {len(incentives)} scheme file(s) | rows before={before} "
            f"after={after if not (dry_run and owns_session) else before} | {total.summary()}"
            f"{' (dry run, nothing written)' if dry_run else ''}"
        )
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
