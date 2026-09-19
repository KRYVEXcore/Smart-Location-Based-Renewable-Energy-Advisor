"""Loads verified tariff schedules from backend/app/data/tariffs/india/ into
the electricity_tariffs table.

Not wired into app startup by default: seeding real regulatory data is a
deliberate, reviewed action. Every file is validated first (official source,
complete provenance, slabs, dates, DISCOM registered) and nothing is written
if any file fails.

Idempotent and non-destructive: each slab is upserted by its natural key
(state/UT, DISCOM, category, tariff_version, slab_min_kwh), so running this
twice changes nothing. A slab that is no longer in a schedule's file is
deactivated, never deleted, so old calculations stay reproducible.

Run from backend/ with:

    python -m scripts.seed_tariffs [--dry-run] [--expect-database NAME]
"""

import argparse
from decimal import Decimal

from sqlalchemy.orm import Session

from app.data_validation import dataset
from app.data_validation.records import TariffScheduleRecord
from app.database.connection import SessionLocal
from app.models.discom import Discom
from app.models.electricity_tariff import ElectricityTariff
from scripts._seed_common import (
    SeedStats,
    add_common_arguments,
    assert_expected_database,
    describe_database,
    sync_attributes,
)

NUMERIC_FIELDS = {
    "slab_max_kwh",
    "energy_charge_inr_per_kwh",
    "fixed_charge_inr",
    "wheeling_charge_inr_per_kwh",
}


def resolve_discom_id(session: Session, schedule: TariffScheduleRecord):
    if schedule.discom_short_code is None:
        return None
    query = session.query(Discom).filter(Discom.short_code == schedule.discom_short_code)
    query = query.filter(Discom.state == schedule.state) if schedule.state else query.filter(
        Discom.union_territory == schedule.union_territory
    )
    discom = query.one_or_none()
    if discom is None:
        raise ValueError(
            f"DISCOM {schedule.discom_short_code!r} is not in the database for "
            f"{schedule.state or schedule.union_territory!r}: run scripts.seed_discoms first."
        )
    return discom.id


def load_schedule(session: Session, schedule: TariffScheduleRecord) -> SeedStats:
    stats = SeedStats()
    discom_id = resolve_discom_id(session, schedule)

    existing = (
        session.query(ElectricityTariff)
        .filter(
            ElectricityTariff.state == schedule.state,
            ElectricityTariff.union_territory == schedule.union_territory,
            ElectricityTariff.discom_id == discom_id,
            ElectricityTariff.consumer_category == schedule.consumer_category,
            ElectricityTariff.tariff_version == schedule.tariff_version,
        )
        .all()
    )
    by_min = {Decimal(str(row.slab_min_kwh)): row for row in existing}
    source = schedule.source
    seen_mins: set[Decimal] = set()

    for slab in schedule.slabs:
        seen_mins.add(Decimal(str(slab.slab_min_kwh)))
        desired = {
            "tariff_name": schedule.tariff_name,
            "slab_max_kwh": slab.slab_max_kwh,
            "energy_charge_inr_per_kwh": slab.energy_charge_inr_per_kwh,
            "fixed_charge_inr": slab.fixed_charge_inr,
            "fixed_charge_basis": schedule.fixed_charge_basis.value if schedule.fixed_charge_basis else None,
            "wheeling_charge_inr_per_kwh": slab.wheeling_charge_inr_per_kwh,
            "effective_from": schedule.effective_from,
            "effective_to": schedule.effective_to,
            "source_name": source.name,
            "source_url": source.url,
            "source_document": source.document,
            "source_order_number": source.order_number,
            "source_order_date": source.order_date,
            "source_page": source.page,
            "source_table": source.table,
            "source_section": source.section,
            "source_excerpt": source.excerpt,
            "verification_notes": schedule.verification_notes,
            "last_verified": source.last_verified,
            "verification_status": schedule.verification_status,
            "active": schedule.active,
        }
        row = by_min.get(Decimal(str(slab.slab_min_kwh)))
        if row is None:
            session.add(
                ElectricityTariff(
                    state=schedule.state,
                    union_territory=schedule.union_territory,
                    discom_id=discom_id,
                    consumer_category=schedule.consumer_category,
                    tariff_version=schedule.tariff_version,
                    slab_min_kwh=slab.slab_min_kwh,
                    **desired,
                )
            )
            stats.inserted += 1
        elif sync_attributes(row, desired, NUMERIC_FIELDS):
            stats.updated += 1
        else:
            stats.unchanged += 1

    for slab_min, row in by_min.items():
        if slab_min not in seen_mins and row.active:
            row.active = False
            stats.deactivated += 1

    return stats


def seed_all(
    *, dry_run: bool = False, expect_database: str | None = None, session: Session | None = None
) -> SeedStats:
    """With `session` given (see scripts.seed_all) the caller owns commit/rollback,
    so several steps can share one transaction.
    """
    tariffs = dataset.load_tariff_schedules()
    discoms = dataset.load_discom_records()
    problems = dataset.check_tariff_dataset(tariffs, dataset.known_discom_keys(discoms))
    if problems:
        raise SystemExit("Tariff data failed validation, nothing written:\n  " + "\n  ".join(problems))

    owns_session = session is None
    session = session or SessionLocal()
    total = SeedStats()
    try:
        assert_expected_database(session, expect_database)
        print(f"[tariffs] target: {describe_database(session)}")
        before = session.query(ElectricityTariff).count()
        for _, schedule in tariffs:
            total.add(load_schedule(session, schedule))
            session.flush()
        after = session.query(ElectricityTariff).count()
        if owns_session:
            session.rollback() if dry_run else session.commit()
        print(
            f"[tariffs] {len(tariffs)} schedule file(s) | rows before={before} "
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
