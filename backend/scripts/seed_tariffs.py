"""Loads verified tariff schedules from backend/app/data/tariffs/india/ into
the electricity_tariffs table.

Not wired into app startup — seeding real regulatory data is a deliberate,
reviewed action, not something that should silently run on every boot.
Safe to re-run: each (state/UT, DISCOM, category, tariff_version) schedule
is replaced wholesale rather than diffed row by row.

Run from backend/ with:

    python -m scripts.seed_tariffs

As of Phase 5, backend/app/data/tariffs/india/ contains no real state data
(see its README.md for the investigation record) — running this script
today is a documented no-op, not an error.
"""

import json
from decimal import Decimal
from pathlib import Path

from app.database.connection import SessionLocal
from app.engines.tariff.validation import validate_slabs
from app.models.discom import Discom
from app.models.electricity_tariff import ElectricityTariff
from app.models.enums import TariffConsumerCategory
from app.schemas.tariff import TariffSlabInput

DATA_ROOT = Path(__file__).resolve().parent.parent / "app" / "data" / "tariffs" / "india"


def _resolve_discom_id(session, short_code: str | None, state: str | None, union_territory: str | None):
    if short_code is None:
        return None
    query = session.query(Discom).filter(Discom.short_code == short_code)
    if state:
        query = query.filter(Discom.state == state)
    elif union_territory:
        query = query.filter(Discom.union_territory == union_territory)
    discom = query.one_or_none()
    if discom is None:
        raise ValueError(f"No DISCOM found with short_code={short_code!r} in {state or union_territory!r}")
    return discom.id


def _load_schedule_file(session, path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))

    consumer_category = TariffConsumerCategory(payload["consumer_category"])
    discom_id = _resolve_discom_id(
        session, payload.get("discom_short_code"), payload.get("state"), payload.get("union_territory")
    )

    slab_inputs = [
        TariffSlabInput(
            tariff_version=payload["tariff_version"],
            tariff_name=payload["tariff_name"],
            slab_min_kwh=Decimal(str(slab["slab_min_kwh"])),
            slab_max_kwh=None if slab.get("slab_max_kwh") is None else Decimal(str(slab["slab_max_kwh"])),
            energy_charge_inr_per_kwh=Decimal(str(slab["energy_charge_inr_per_kwh"])),
            fixed_charge_inr=(
                None if slab.get("fixed_charge_inr") is None else Decimal(str(slab["fixed_charge_inr"]))
            ),
            wheeling_charge_inr_per_kwh=(
                None
                if slab.get("wheeling_charge_inr_per_kwh") is None
                else Decimal(str(slab["wheeling_charge_inr_per_kwh"]))
            ),
            effective_from=payload["effective_from"],
            effective_to=payload.get("effective_to"),
            source_url=payload.get("source_url"),
            source_document=payload.get("source_document"),
            source_name=payload.get("source_name"),
            last_verified=payload.get("last_verified"),
        )
        for slab in payload["slabs"]
    ]
    # Fail loudly on malformed seed data rather than writing bad rows.
    validate_slabs(slab_inputs)

    # Replace any existing rows for this exact schedule so the script is
    # safely re-runnable as source data is corrected.
    session.query(ElectricityTariff).filter(
        ElectricityTariff.state == payload.get("state"),
        ElectricityTariff.union_territory == payload.get("union_territory"),
        ElectricityTariff.discom_id == discom_id,
        ElectricityTariff.consumer_category == consumer_category,
        ElectricityTariff.tariff_version == payload["tariff_version"],
    ).delete()

    for slab_input in slab_inputs:
        session.add(
            ElectricityTariff(
                state=payload.get("state"),
                union_territory=payload.get("union_territory"),
                discom_id=discom_id,
                consumer_category=consumer_category,
                tariff_version=slab_input.tariff_version,
                tariff_name=slab_input.tariff_name,
                slab_min_kwh=slab_input.slab_min_kwh,
                slab_max_kwh=slab_input.slab_max_kwh,
                energy_charge_inr_per_kwh=slab_input.energy_charge_inr_per_kwh,
                fixed_charge_inr=slab_input.fixed_charge_inr,
                wheeling_charge_inr_per_kwh=slab_input.wheeling_charge_inr_per_kwh,
                effective_from=slab_input.effective_from,
                effective_to=slab_input.effective_to,
                source_url=slab_input.source_url,
                source_document=slab_input.source_document,
                source_name=slab_input.source_name,
                last_verified=slab_input.last_verified,
                active=True,
            )
        )
    return len(slab_inputs)


def seed_all() -> None:
    session = SessionLocal()
    total_files = 0
    total_slabs = 0
    try:
        for schedule_file in sorted(DATA_ROOT.glob("*/*.json")):
            total_slabs += _load_schedule_file(session, schedule_file)
            total_files += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    print(f"Loaded {total_files} tariff schedule file(s), {total_slabs} slab row(s).")


if __name__ == "__main__":
    seed_all()
