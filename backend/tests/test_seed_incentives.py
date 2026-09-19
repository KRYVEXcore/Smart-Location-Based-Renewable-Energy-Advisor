"""Seed-script behavior against the isolated test database: idempotent
upsert, in-place update, no deletion. Uses synthetic fixture records only —
never the real files in backend/app/data/incentives/india/ (those are
covered by tests/test_real_seed_data.py).
"""

from copy import deepcopy
from decimal import Decimal

import pytest

from app.data_validation import dataset
from app.data_validation.records import IncentiveRecord
from app.models.incentive_program import IncentiveProgram
from scripts.seed_incentives import load_scheme

NAME = "TEST FIXTURE ONLY - Seed Scheme"

BASE_PAYLOAD = {
    "scheme_name": NAME,
    "scheme_version": "TEST-SEED-2026.1",
    "description": "TEST fixture only.",
    "level": "central",
    "incentive_type": "capital_subsidy",
    "consumer_category": "residential",
    "technology": "solar",
    "max_system_size_kw": Decimal("3"),
    "subsidy_type": "fixed_amount",
    "subsidy_value": Decimal("15000"),
    "effective_from": "2026-01-01",
    "verification_status": "verified",
    "active": True,
    "source": {
        "name": "TEST fixture ministry",
        "url": "https://example.gov.in/test-fixture.pdf",
        "document": "TEST fixture document",
        "order_number": "TEST/1/2026",
        "page": "1",
        "table": "TEST table",
        "excerpt": "TEST excerpt",
        "last_verified": "2026-01-01",
    },
}


def _record(**overrides) -> IncentiveRecord:
    payload = deepcopy(BASE_PAYLOAD)
    payload.update(overrides)
    return IncentiveRecord.model_validate(payload)


def _rows(db_session):
    return db_session.query(IncentiveProgram).filter(IncentiveProgram.scheme_name == NAME).all()


def test_loading_the_same_scheme_twice_does_not_duplicate_it(db_session):
    first = load_scheme(db_session, _record())
    db_session.commit()
    second = load_scheme(db_session, _record())
    db_session.commit()

    assert (first.inserted, first.updated) == (1, 0)
    assert (second.inserted, second.updated, second.unchanged) == (0, 0, 1)
    assert len(_rows(db_session)) == 1


def test_an_updated_record_changes_the_row_in_place(db_session):
    load_scheme(db_session, _record())
    db_session.commit()

    stats = load_scheme(db_session, _record(subsidy_value=Decimal("20000")))
    db_session.commit()

    rows = _rows(db_session)
    assert stats.updated == 1
    assert len(rows) == 1
    assert rows[0].subsidy_value == Decimal("20000")


def test_a_new_scheme_version_is_added_and_the_old_one_is_kept(db_session):
    load_scheme(db_session, _record(scheme_version="TEST-SEED-2026.1", effective_to="2026-12-31"))
    load_scheme(db_session, _record(scheme_version="TEST-SEED-2027.1", effective_from="2027-01-01"))
    db_session.commit()

    assert sorted(row.scheme_version for row in _rows(db_session)) == ["TEST-SEED-2026.1", "TEST-SEED-2027.1"]


def test_the_seed_never_deletes_rows_it_does_not_know_about(db_session):
    load_scheme(
        db_session, _record(scheme_version="TEST-SEED-OLD", effective_from="2024-01-01", effective_to="2025-12-31")
    )
    db_session.commit()

    load_scheme(db_session, _record(scheme_version="TEST-SEED-NEW"))
    db_session.commit()

    assert len(_rows(db_session)) == 2


def test_slab_based_record_with_invalid_slabs_is_reported_by_the_dataset_check():
    record = _record(
        subsidy_type="slab_based",
        subsidy_value=None,
        calculation_rules={"slabs": [{"capacity_min_kw": 1, "capacity_max_kw": 2, "rate_inr_per_kw": 30000}]},
    )

    problems = dataset.check_incentive_dataset([(_path("bad-slabs.json"), record)])

    assert any("invalid capacity slabs" in problem for problem in problems)


def test_an_unverified_record_cannot_be_active():
    with pytest.raises(ValueError, match="unverified record must not be active"):
        _record(verification_status="pending_review", active=True)


def _path(name):
    from pathlib import Path

    return Path(name)
