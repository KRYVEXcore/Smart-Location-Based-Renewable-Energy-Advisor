"""Loads verified incentive programmes from
backend/app/data/incentives/india/ into the incentive_programs table.

Not wired into app startup — seeding real government scheme data is a
deliberate, reviewed action, not something that should silently run on
every boot. Safe to re-run: each (scheme_name, level, technology,
scheme_version) is replaced wholesale rather than diffed row by row, so
running this script twice never duplicates a programme.

Run from backend/ with:

    python -m scripts.seed_incentives

As of Phase 6, backend/app/data/incentives/india/ contains no real scheme
data (see its README.md for the investigation record) — running this
script today is a documented no-op, not an error.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.database.connection import SessionLocal
from app.engines.incentive.calculator import parse_capacity_slabs
from app.engines.incentive.validation import validate_capacity_slabs
from app.models.discom import Discom
from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)
from app.models.incentive_program import IncentiveProgram

DATA_ROOT = Path(__file__).resolve().parent.parent / "app" / "data" / "incentives" / "india"
SCHEME_GLOBS = ["central/*.json", "states/*/*.json", "discom/*/*.json"]


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


def _load_scheme_file(session, path: Path) -> None:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))

    level = IncentiveLevel(payload["level"])
    technology = RenewableTechnology(payload["technology"])
    consumer_category = (
        None if payload.get("consumer_category") is None else TariffConsumerCategory(payload["consumer_category"])
    )
    subsidy_type = SubsidyType(payload["subsidy_type"])
    incentive_type = IncentiveType(payload["incentive_type"])
    verification_status = IncentiveVerificationStatus(payload["verification_status"])
    discom_id = _resolve_discom_id(
        session, payload.get("discom_short_code"), payload.get("state"), payload.get("union_territory")
    )

    calculation_rules = payload.get("calculation_rules")
    if subsidy_type == SubsidyType.SLAB_BASED:
        # Fail loudly on malformed seed data rather than writing bad rows.
        slabs = parse_capacity_slabs(calculation_rules)
        if slabs is None:
            raise ValueError(f"{path}: slab_based scheme is missing calculation_rules.slabs")
        validate_capacity_slabs(slabs)

    # Replace any existing row for this exact scheme version so the script
    # is safely re-runnable as source data is corrected.
    session.query(IncentiveProgram).filter(
        IncentiveProgram.scheme_name == payload["scheme_name"],
        IncentiveProgram.level == level,
        IncentiveProgram.technology == technology,
        IncentiveProgram.scheme_version == payload["scheme_version"],
    ).delete()

    session.add(
        IncentiveProgram(
            scheme_name=payload["scheme_name"],
            scheme_version=payload["scheme_version"],
            description=payload.get("description"),
            level=level,
            incentive_type=incentive_type,
            state=payload.get("state"),
            union_territory=payload.get("union_territory"),
            discom_id=discom_id,
            consumer_category=consumer_category,
            technology=technology,
            min_system_size_kw=_decimal_or_none(payload.get("min_system_size_kw")),
            max_system_size_kw=_decimal_or_none(payload.get("max_system_size_kw")),
            subsidy_type=subsidy_type,
            subsidy_value=_decimal_or_none(payload.get("subsidy_value")),
            percentage_value=_decimal_or_none(payload.get("percentage_value")),
            maximum_amount=_decimal_or_none(payload.get("maximum_amount")),
            calculation_rules=calculation_rules,
            eligibility_rules=payload.get("eligibility_rules"),
            application_requirements=payload.get("application_requirements"),
            stacking_rules=payload.get("stacking_rules"),
            effective_from=date.fromisoformat(payload["effective_from"]),
            effective_to=_date_or_none(payload.get("effective_to")),
            verification_status=verification_status,
            source_name=payload.get("source_name"),
            source_url=payload.get("source_url"),
            source_document=payload.get("source_document"),
            last_verified=_date_or_none(payload.get("last_verified")),
            active=payload.get("active", True),
        )
    )


def _decimal_or_none(value) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _date_or_none(value: str | None) -> date | None:
    return None if value is None else date.fromisoformat(value)


def seed_all() -> None:
    session = SessionLocal()
    total = 0
    try:
        for pattern in SCHEME_GLOBS:
            for scheme_file in sorted(DATA_ROOT.glob(pattern)):
                _load_scheme_file(session, scheme_file)
                total += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    print(f"Loaded {total} incentive programme file(s).")


if __name__ == "__main__":
    seed_all()
