"""Tests the seed script's idempotency logic directly against the shared
test database session — never against real Postgres or the real
backend/app/data/incentives/india/ directory (which has no real files
yet; see its README.md).
"""

from datetime import date

from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)
from app.models.incentive_program import IncentiveProgram
from scripts.seed_incentives import _load_scheme_file
import json
import pathlib


def _write_fixture(tmp_path: pathlib.Path, **overrides) -> pathlib.Path:
    payload = {
        "scheme_name": "TEST FIXTURE ONLY — Seed Scheme",
        "scheme_version": "TEST-SEED-2026.1",
        "description": "TEST fixture only.",
        "level": "central",
        "incentive_type": "capital_subsidy",
        "state": None,
        "union_territory": None,
        "discom_short_code": None,
        "consumer_category": "residential",
        "technology": "solar",
        "min_system_size_kw": None,
        "max_system_size_kw": 3,
        "subsidy_type": "fixed_amount",
        "subsidy_value": 15000,
        "percentage_value": None,
        "maximum_amount": None,
        "calculation_rules": None,
        "eligibility_rules": None,
        "application_requirements": None,
        "stacking_rules": None,
        "effective_from": "2026-01-01",
        "effective_to": None,
        "verification_status": "verified",
        "source_name": "TEST fixture",
        "source_url": "https://example.invalid/test",
        "source_document": "TEST fixture",
        "last_verified": "2026-01-01",
        "active": True,
    }
    payload.update(overrides)
    path = tmp_path / "scheme.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loading_the_same_scheme_file_twice_does_not_duplicate_it(db_session, tmp_path):
    fixture = _write_fixture(tmp_path)

    _load_scheme_file(db_session, fixture)
    db_session.commit()
    _load_scheme_file(db_session, fixture)
    db_session.commit()

    rows = (
        db_session.query(IncentiveProgram)
        .filter(IncentiveProgram.scheme_name == "TEST FIXTURE ONLY — Seed Scheme")
        .all()
    )
    assert len(rows) == 1
    assert float(rows[0].subsidy_value) == 15000


def test_loading_an_updated_scheme_file_replaces_the_old_row(db_session, tmp_path):
    fixture = _write_fixture(tmp_path, subsidy_value=15000)
    _load_scheme_file(db_session, fixture)
    db_session.commit()

    updated_fixture = _write_fixture(tmp_path, subsidy_value=20000)
    _load_scheme_file(db_session, updated_fixture)
    db_session.commit()

    rows = (
        db_session.query(IncentiveProgram)
        .filter(IncentiveProgram.scheme_name == "TEST FIXTURE ONLY — Seed Scheme")
        .all()
    )
    assert len(rows) == 1
    assert float(rows[0].subsidy_value) == 20000


def test_slab_based_seed_file_with_invalid_slabs_raises(db_session, tmp_path):
    fixture = _write_fixture(
        tmp_path,
        subsidy_type="slab_based",
        calculation_rules={"slabs": [{"capacity_min_kw": 1, "capacity_max_kw": 2, "rate_inr_per_kw": 30000}]},
    )

    try:
        _load_scheme_file(db_session, fixture)
        raised = False
    except ValueError:
        raised = True
    assert raised, "Expected a ValueError for a slab list that doesn't start at 0 kW"
