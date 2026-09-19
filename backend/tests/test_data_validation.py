"""The data-quality gate: each way a tariff/incentive/DISCOM record can be
wrong must be rejected, using synthetic records (the real files are checked
in tests/test_real_seed_data.py).
"""

import copy
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.data_validation import dataset
from app.data_validation.official_sources import is_official_source_url
from app.data_validation.records import (
    DiscomRecord,
    IncentiveRecord,
    TariffScheduleRecord,
    load_json,
)
from app.engines.incentive.scope import applies_to_region

SOURCE = {
    "name": "Test Regulatory Commission",
    "url": "https://www.example.gov.in/order.pdf",
    "document": "Test Order",
    "order_number": "Order 1 of 2026",
    "order_date": "2026-01-01",
    "page": "12",
    "table": "Domestic tariff",
    "excerpt": "0-100 units Rs 4.00 per unit",
    "last_verified": "2026-09-19",
}

TARIFF = {
    "state": "Tamil Nadu",
    "consumer_category": "residential",
    "tariff_version": "T-1",
    "tariff_name": "Test",
    "effective_from": "2026-01-01",
    "fixed_charge_basis": "inr_per_month",
    "verification_status": "verified",
    "active": True,
    "source": SOURCE,
    "slabs": [
        {"slab_min_kwh": Decimal("0"), "slab_max_kwh": Decimal("100"), "energy_charge_inr_per_kwh": Decimal("4"), "fixed_charge_inr": Decimal("10")},
        {"slab_min_kwh": Decimal("100"), "slab_max_kwh": None, "energy_charge_inr_per_kwh": Decimal("6"), "fixed_charge_inr": Decimal("10")},
    ],
}

INCENTIVE = {
    "scheme_name": "Test Scheme",
    "scheme_version": "S-1",
    "level": "central",
    "incentive_type": "capital_subsidy",
    "consumer_category": "residential",
    "technology": "solar",
    "subsidy_type": "fixed_amount",
    "subsidy_value": Decimal("1000"),
    "effective_from": "2026-01-01",
    "verification_status": "verified",
    "active": True,
    "source": SOURCE,
}


def tariff(**overrides) -> TariffScheduleRecord:
    payload = copy.deepcopy(TARIFF)
    payload.update(overrides)
    return TariffScheduleRecord.model_validate(payload)


def incentive(**overrides) -> IncentiveRecord:
    payload = copy.deepcopy(INCENTIVE)
    payload.update(overrides)
    return IncentiveRecord.model_validate(payload)


def source(**overrides) -> dict:
    return {**SOURCE, **overrides}


def path(name: str) -> Path:
    return Path(name)


# ---------------------------------------------------------------- sources


@pytest.mark.parametrize(
    "url, official",
    [
        ("https://www.tnerc.tn.gov.in/x.pdf", True),
        ("https://mnre.gov.in/x", True),
        ("https://cdnbbsr.s3waas.gov.in/x.pdf", True),
        ("https://www.tnpdcl.org/page", True),
        ("https://www.mahadiscom.in/x.pdf", True),
        ("https://kseb.in/x.pdf", True),
        ("https://www.solarquarter.com/tariff", False),
        ("https://calculator-site.example.com/x", False),
        ("https://en.wikipedia.org/wiki/x", False),
        ("http://www.tnerc.tn.gov.in/x.pdf", False),
        ("https://gov.in.attacker.com/x", False),
        ("https://notgov.in/x", False),
        ("", False),
        (None, False),
    ],
)
def test_only_official_hosts_count_as_a_source(url, official):
    assert is_official_source_url(url) is official


def test_a_verified_record_citing_a_commercial_site_is_rejected():
    with pytest.raises(ValidationError, match="not an official Indian source"):
        tariff(source=source(url="https://www.solar-blog.com/tariff"))


@pytest.mark.parametrize("field", ["name", "url", "document", "order_number", "page", "excerpt", "last_verified"])
def test_a_verified_record_missing_any_source_field_is_rejected(field):
    with pytest.raises(ValidationError, match=f"source.{field} is required"):
        tariff(source=source(**{field: None}))


def test_a_verified_record_needs_a_table_or_section():
    with pytest.raises(ValidationError, match="table or source.section"):
        tariff(source=source(table=None, section=None))


def test_a_section_is_enough_locator_without_a_table():
    assert tariff(source=source(table=None, section="Clause 5(h)")).source.section == "Clause 5(h)"


# ------------------------------------------------- status / dates / numbers


def test_an_unverified_tariff_cannot_be_active():
    with pytest.raises(ValidationError, match="unverified record must not be active"):
        tariff(verification_status="pending_review", active=True)


def test_an_unverified_inactive_record_may_lack_a_source():
    record = tariff(verification_status="pending_review", active=False, source={})
    assert record.verification_status.value == "pending_review"


def test_effective_to_before_effective_from_is_rejected():
    with pytest.raises(ValidationError, match="effective_to is before effective_from"):
        tariff(effective_to="2025-12-31")


def test_a_float_number_is_rejected_in_favour_of_decimal():
    payload = copy.deepcopy(TARIFF)
    payload["slabs"][0]["energy_charge_inr_per_kwh"] = 4.95
    with pytest.raises(ValidationError, match="never float"):
        TariffScheduleRecord.model_validate(payload)


def test_load_json_parses_numbers_as_exact_decimals(tmp_path):
    file = tmp_path / "x.json"
    file.write_text('{"rate": 4.95, "n": 3}', encoding="utf-8")

    data = load_json(file)

    assert data["rate"] == Decimal("4.95") and isinstance(data["rate"], Decimal)


def test_a_fixed_charge_without_a_basis_is_rejected():
    with pytest.raises(ValidationError, match="fixed_charge_basis is required"):
        tariff(fixed_charge_basis=None)


def test_an_unknown_fixed_charge_basis_is_rejected():
    with pytest.raises(ValidationError):
        tariff(fixed_charge_basis="per_moon_phase")


def test_an_unknown_consumer_category_is_rejected():
    with pytest.raises(ValidationError):
        tariff(consumer_category="galactic")


@pytest.mark.parametrize("state", ["Atlantis", "tamil nadu", ""])
def test_an_unknown_or_non_canonical_state_is_rejected(state):
    with pytest.raises(ValidationError, match="Unknown state"):
        tariff(state=state)


def test_exactly_one_of_state_and_union_territory_is_required():
    with pytest.raises(ValidationError, match="Exactly one"):
        tariff(union_territory="Delhi")


# ------------------------------------------------------------------ slabs


def _slab(low, high, rate="5"):
    return {
        "slab_min_kwh": Decimal(low),
        "slab_max_kwh": None if high is None else Decimal(high),
        "energy_charge_inr_per_kwh": Decimal(rate),
    }


def test_a_gap_between_slabs_is_reported():
    record = tariff(slabs=[_slab("0", "100"), _slab("150", None)], fixed_charge_basis=None)

    problems = dataset.check_tariff_dataset([(path("gap.json"), record)])

    assert any("contiguous" in p for p in problems)


def test_overlapping_slabs_are_reported():
    record = tariff(slabs=[_slab("0", "120"), _slab("100", None)], fixed_charge_basis=None)

    problems = dataset.check_tariff_dataset([(path("overlap.json"), record)])

    assert any("invalid slabs" in p for p in problems)


def test_slabs_that_do_not_start_at_zero_are_reported():
    record = tariff(slabs=[_slab("10", None)], fixed_charge_basis=None)

    assert any("start at 0" in p for p in dataset.check_tariff_dataset([(path("start.json"), record)]))


def test_two_unlimited_slabs_are_reported():
    record = tariff(slabs=[_slab("0", None), _slab("100", None)], fixed_charge_basis=None)

    assert dataset.check_tariff_dataset([(path("two-open.json"), record)])


# -------------------------------------------- duplicates / overlapping periods


def test_a_duplicate_tariff_schedule_key_is_reported():
    first, second = tariff(), tariff()

    problems = dataset.check_tariff_dataset([(path("a.json"), first), (path("b.json"), second)])

    assert any("duplicate schedule" in p for p in problems)


def test_overlapping_effective_periods_for_the_same_scope_are_reported():
    older = tariff(tariff_version="T-1", effective_from="2026-01-01", effective_to="2026-12-31")
    newer = tariff(tariff_version="T-2", effective_from="2026-06-01")

    problems = dataset.check_tariff_dataset([(path("a.json"), older), (path("b.json"), newer)])

    assert any("overlapping effective periods" in p for p in problems)


def test_back_to_back_versions_do_not_overlap():
    older = tariff(tariff_version="T-1", effective_from="2026-01-01", effective_to="2026-03-31")
    newer = tariff(tariff_version="T-2", effective_from="2026-04-01")

    assert dataset.check_tariff_dataset([(path("a.json"), older), (path("b.json"), newer)]) == []


def test_the_same_dates_for_a_different_state_do_not_overlap():
    a = tariff(state="Tamil Nadu")
    b = tariff(state="Kerala", tariff_version="T-1")

    assert dataset.check_tariff_dataset([(path("a.json"), a), (path("b.json"), b)]) == []


def test_a_tariff_naming_an_unregistered_discom_is_reported():
    record = tariff(discom_short_code="GHOST")

    problems = dataset.check_tariff_dataset([(path("d.json"), record)], known_discoms={("TNPDCL", "Tamil Nadu")})

    assert any("not registered" in p for p in problems)


def test_a_discom_registered_for_another_state_is_not_accepted():
    record = tariff(discom_short_code="TNPDCL", state="Karnataka")

    problems = dataset.check_tariff_dataset([(path("d.json"), record)], known_discoms={("TNPDCL", "Tamil Nadu")})

    assert any("not registered" in p for p in problems)


def test_a_duplicate_incentive_scheme_version_is_reported():
    problems = dataset.check_incentive_dataset([(path("a.json"), incentive()), (path("b.json"), incentive())])

    assert any("duplicate scheme version" in p for p in problems)


def test_overlapping_incentive_versions_applying_in_the_same_region_are_reported():
    a = incentive(scheme_version="S-1", effective_from="2026-01-01")
    b = incentive(scheme_version="S-2", effective_from="2026-06-01")

    problems = dataset.check_incentive_dataset([(path("a.json"), a), (path("b.json"), b)])

    assert any("overlapping periods" in p for p in problems)


def test_regional_variants_with_disjoint_regions_may_overlap_in_time():
    rest = incentive(scheme_version="S-STD", eligibility_rules={"excluded_states": ["Sikkim"]})
    special = incentive(scheme_version="S-SPECIAL", eligibility_rules={"applies_only_to_states": ["Sikkim"]})

    assert dataset.check_incentive_dataset([(path("a.json"), rest), (path("b.json"), special)]) == []


def test_a_slab_incentive_needs_valid_capacity_slabs():
    record = incentive(
        subsidy_type="slab_based",
        subsidy_value=None,
        calculation_rules={"slabs": [{"capacity_min_kw": 0, "capacity_max_kw": 2, "rate_inr_per_kw": 30000},
                                     {"capacity_min_kw": 3, "capacity_max_kw": None, "rate_inr_per_kw": 1}]},
    )

    assert any("invalid capacity slabs" in p for p in dataset.check_incentive_dataset([(path("s.json"), record)]))


def test_a_state_level_incentive_needs_a_state():
    with pytest.raises(ValidationError, match="needs a state"):
        incentive(level="state")


def test_a_per_kw_incentive_without_a_value_is_reported():
    record = incentive(subsidy_type="per_kw", subsidy_value=None)

    assert any("no subsidy_value" in p for p in dataset.check_incentive_dataset([(path("k.json"), record)]))


# ----------------------------------------------------------------- DISCOMs


def test_a_discom_needs_an_official_source_document_and_verification_date():
    base = {"name": "X", "short_code": "X", "state": "Kerala", "source": SOURCE}
    assert DiscomRecord.model_validate(base).short_code == "X"

    with pytest.raises(ValidationError, match="official source URL"):
        DiscomRecord.model_validate({**base, "source": source(url="https://blog.example.com/x")})
    with pytest.raises(ValidationError, match="verified"):
        DiscomRecord.model_validate({**base, "source": source(last_verified=None)})


def test_a_duplicate_discom_is_reported():
    record = DiscomRecord.model_validate({"name": "X", "short_code": "X", "state": "Kerala", "source": SOURCE})

    problems = dataset.check_discom_dataset([(path("a.json"), record), (path("b.json"), record)])

    assert any("duplicate DISCOM" in p for p in problems)


# ------------------------------------------------------- region scoping


def program(state=None, union_territory=None, **rules):
    return SimpleNamespace(state=state, union_territory=union_territory, eligibility_rules=rules or None)


def test_an_unscoped_programme_applies_everywhere():
    assert applies_to_region(program(), state="Kerala", union_territory=None)
    assert applies_to_region(program(), state=None, union_territory="Delhi")
    assert applies_to_region(program(), state=None, union_territory=None)


def test_a_programme_with_its_own_state_applies_only_there():
    assert applies_to_region(program(state="Kerala"), state="Kerala", union_territory=None)
    assert not applies_to_region(program(state="Kerala"), state="Assam", union_territory=None)
    assert not applies_to_region(program(state="Kerala"), state=None, union_territory="Delhi")


def test_excluded_states_and_union_territories_do_not_apply():
    rules = dict(excluded_states=["Sikkim"], excluded_union_territories=["Ladakh"])

    assert not applies_to_region(program(**rules), state="Sikkim", union_territory=None)
    assert not applies_to_region(program(**rules), state=None, union_territory="Ladakh")
    assert applies_to_region(program(**rules), state="Kerala", union_territory=None)


def test_applies_only_to_lists_restrict_to_those_regions():
    rules = dict(applies_only_to_states=["Sikkim"], applies_only_to_union_territories=["Ladakh"])

    assert applies_to_region(program(**rules), state="Sikkim", union_territory=None)
    assert applies_to_region(program(**rules), state=None, union_territory="Ladakh")
    assert not applies_to_region(program(**rules), state="Kerala", union_territory=None)


def test_a_restricted_programme_never_applies_to_an_unresolved_location():
    rules = dict(applies_only_to_states=["Sikkim"])

    assert not applies_to_region(program(**rules), state=None, union_territory=None)
