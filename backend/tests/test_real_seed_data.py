"""Tests of the REAL seed data in backend/app/data/ (tariffs, incentives,
DISCOMs): data quality, hand-calculated bills, version selection, seed
idempotency, and end-to-end API behavior.

The expected numbers below were calculated by hand from the official
figures quoted in docs/data-verification/tariff-and-incentive-research.md,
independently of the engine.
"""

import copy
from datetime import date
from decimal import Decimal

import pytest

from app.core.india_geography import INDIAN_STATES, INDIAN_UNION_TERRITORIES
from app.data_validation import dataset
from app.data_validation.official_sources import is_official_source_url
from app.database.repositories.discom_repository import DiscomRepository
from app.engines.tariff.tariff_engine import calculate_bill_for_grid_consumption
from app.main import app
from app.models.discom import Discom
from app.models.electricity_tariff import ElectricityTariff
from app.models.enums import IncentiveVerificationStatus, TariffConsumerCategory
from app.models.incentive_program import IncentiveProgram
from app.schemas.location import GeocodingCandidate
from app.services.location.dependencies import get_location_service
from app.services.location.india_resolver import IndiaLocationResolver
from scripts import seed_discoms, seed_incentives, seed_tariffs
from tests.location_fakes import FakeGeocodingProvider, make_test_location_service

TARIFFS = dataset.load_tariff_schedules()
INCENTIVES = dataset.load_incentive_records()
DISCOMS = dataset.load_discom_records()

RESIDENTIAL = TariffConsumerCategory.RESIDENTIAL


def _ids(loaded):
    return [path.name for path, _ in loaded]


# ----------------------------------------------------------------- data quality


def test_dataset_passes_every_cross_record_check():
    problems = (
        dataset.check_discom_dataset(DISCOMS)
        + dataset.check_tariff_dataset(TARIFFS, dataset.known_discom_keys(DISCOMS))
        + dataset.check_incentive_dataset(INCENTIVES)
    )
    assert problems == []


def test_the_dataset_is_not_empty_and_every_record_is_verified():
    assert TARIFFS and INCENTIVES and DISCOMS
    for _, record in TARIFFS + INCENTIVES:
        assert record.verification_status == IncentiveVerificationStatus.VERIFIED


@pytest.mark.parametrize("loaded", TARIFFS + INCENTIVES, ids=_ids(TARIFFS + INCENTIVES))
def test_every_record_cites_an_official_source_with_an_exact_locator(loaded):
    _, record = loaded
    source = record.source
    assert is_official_source_url(source.url), source.url
    assert source.name and source.document and source.order_number
    assert source.page and (source.table or source.section)
    assert source.excerpt and len(source.excerpt) > 40
    assert source.last_verified is not None and source.last_verified <= date.today()
    assert record.verification_notes


@pytest.mark.parametrize("loaded", DISCOMS, ids=[record.short_code for _, record in DISCOMS])
def test_every_discom_cites_an_official_source(loaded):
    _, record = loaded
    assert is_official_source_url(record.source.url)
    assert record.source.last_verified is not None


def test_no_unverified_record_is_active():
    for _, record in TARIFFS + INCENTIVES:
        assert record.verification_status == IncentiveVerificationStatus.VERIFIED or not record.active


def test_every_number_is_a_decimal_never_a_float():
    for _, schedule in TARIFFS:
        for slab in schedule.slabs:
            for value in (
                slab.slab_min_kwh,
                slab.slab_max_kwh,
                slab.energy_charge_inr_per_kwh,
                slab.fixed_charge_inr,
                slab.wheeling_charge_inr_per_kwh,
            ):
                assert value is None or isinstance(value, Decimal)
    for _, record in INCENTIVES:
        for slab in record.calculation_rules["slabs"]:
            assert not isinstance(slab["rate_inr_per_kw"], float)


def test_a_fixed_charge_always_states_what_it_is_charged_per():
    for _, schedule in TARIFFS:
        if any(slab.fixed_charge_inr is not None for slab in schedule.slabs):
            assert schedule.fixed_charge_basis is not None


def test_every_tariff_is_scoped_to_exactly_one_state_and_category_is_residential():
    for _, schedule in TARIFFS:
        assert (schedule.state is None) != (schedule.union_territory is None)
        assert schedule.consumer_category == RESIDENTIAL


def test_only_researched_jurisdictions_have_tariffs():
    assert sorted({schedule.state for _, schedule in TARIFFS}) == [
        "Andhra Pradesh",
        "Karnataka",
        "Maharashtra",
        "Rajasthan",
        "Tamil Nadu",
    ]


# ------------------------------------------------------- hand-calculated bills


def _rows(state, discom=None):
    from app.data_validation.dataset import to_slab_inputs

    rows = []
    for _, schedule in TARIFFS:
        if schedule.state == state and schedule.discom_short_code == discom:
            rows.extend(to_slab_inputs(schedule))
    return rows


def _bill(state, kwh, on, discom=None):
    return calculate_bill_for_grid_consumption(Decimal(kwh), _rows(state, discom), on, RESIDENTIAL)


def _component(result, name):
    return next(c for c in result.charges if c.component == name)


def test_tamil_nadu_950_kwh_approved_tariff():
    # 200 @ 4.95 + 50 @ 6.65 + 50 @ 8.80 + 100 @ 9.95 + 100 @ 11.05 + 450 @ 12.15
    # = 990 + 332.50 + 440 + 995 + 1105 + 5467.50 = 9330.00; fixed charge Nil.
    result = _bill("Tamil Nadu", "950", date(2026, 9, 19), discom="TNPDCL")

    assert result.status == "ok"
    assert _component(result, "energy").amount_inr == "9330.00"
    assert _component(result, "fixed").amount_inr == "0.00"
    assert result.estimated_monthly_bill_inr == "9330.00"


def test_tamil_nadu_boundary_consumption_is_billed_in_the_lower_slab():
    result = _bill("Tamil Nadu", "200", date(2026, 9, 19), discom="TNPDCL")

    assert _component(result, "energy").amount_inr == "990.00"  # 200 x 4.95 only


def test_maharashtra_950_kwh_fy2026_27():
    # energy: 100 @ 3.96 + 200 @ 10.80 + 200 @ 15.03 + 450 @ 17.53
    #       = 396 + 2160 + 3006 + 7888.50 = 13450.50
    # wheeling 950 @ 1.60 = 1520.00; fixed Rs 130 per connection.
    result = _bill("Maharashtra", "950", date(2026, 9, 19), discom="MSEDCL")

    assert _component(result, "energy").amount_inr == "13450.50"
    assert _component(result, "wheeling").amount_inr == "1520.00"
    assert _component(result, "fixed").amount_inr == "130.00"
    assert result.estimated_monthly_bill_inr == "15100.50"


def test_karnataka_950_kwh_fixed_charge_is_never_billed_without_sanctioned_load():
    result = _bill("Karnataka", "950", date(2026, 9, 19))

    assert _component(result, "energy").amount_inr == "5510.00"  # 950 x 5.80
    fixed = _component(result, "fixed")
    assert fixed.status == "not_calculated" and fixed.amount_inr is None
    assert "sanctioned load" in fixed.notes
    assert result.estimated_monthly_bill_inr == "5510.00"
    assert result.is_partial_estimate is True
    assert "fixed_charge_not_calculated" in result.excluded_components


def test_andhra_pradesh_950_kwh_fy2026_27_telescopic_slabs():
    # 30 @ 1.90 + 45 @ 3.00 + 50 @ 4.50 + 100 @ 6.00 + 175 @ 8.75 + 550 @ 9.75
    # = 57.00 + 135.00 + 225.00 + 600.00 + 1531.25 + 5362.50 = 7910.75
    result = _bill("Andhra Pradesh", "950", date(2026, 9, 19))

    assert _component(result, "energy").amount_inr == "7910.75"
    fixed = _component(result, "fixed")
    assert fixed.status == "not_calculated" and fixed.amount_inr is None
    assert result.estimated_monthly_bill_inr == "7910.75"


def test_andhra_pradesh_tariff_stops_at_the_end_of_the_order_year():
    assert _bill("Andhra Pradesh", "300", date(2027, 3, 31)).status == "ok"
    assert _bill("Andhra Pradesh", "300", date(2027, 4, 1)).status == "tariff_not_configured"
    assert _bill("Andhra Pradesh", "300", date(2026, 3, 31)).status == "tariff_not_configured"


@pytest.mark.parametrize(
    "kwh, energy, fixed",
    [
        ("40", "190.00", "150.00"),  # 40 x 4.75; bracket up to 150 units
        ("120", "657.50", "150.00"),  # 50 x 4.75 + 70 x 6.00 = 237.50 + 420.00
        ("250", "1537.50", "300.00"),  # 237.50 + 100 x 6.00 + 100 x 7.00 = 237.50 + 600 + 700
        ("950", "6662.50", "800.00"),  # 237.50 + 600 + 1050 + 1400 + 450 x 7.50
    ],
)
def test_rajasthan_bills_follow_progressive_energy_and_bracket_fixed_charge(kwh, energy, fixed):
    result = _bill("Rajasthan", kwh, date(2026, 9, 19))

    assert _component(result, "fixed").amount_inr == fixed
    assert _component(result, "energy").amount_inr == energy


# ------------------------------------------------------ historical versions


@pytest.mark.parametrize(
    "state, discom, before, old_day, new_day, old_version, new_version",
    [
        ("Maharashtra", "MSEDCL", date(2025, 6, 30), date(2025, 12, 1), date(2026, 6, 1),
         "MH-MSEDCL-LT-IB-FY2025-26", "MH-MSEDCL-LT-IB-FY2026-27"),
        ("Karnataka", None, date(2025, 3, 31), date(2025, 12, 1), date(2026, 6, 1),
         "KA-ESCOMS-LT1-FY2025-26", "KA-ESCOMS-LT1-FY2026-27"),
        ("Rajasthan", None, date(2025, 9, 30), date(2025, 12, 1), date(2026, 6, 1),
         "RJ-DISCOMS-LT1-FY2025-26-H2", "RJ-DISCOMS-LT1-FY2026-27"),
    ],
)
def test_calculation_date_selects_the_version_in_force(
    state, discom, before, old_day, new_day, old_version, new_version
):
    assert _bill(state, "300", old_day, discom).tariff.tariff_version == old_version
    assert _bill(state, "300", new_day, discom).tariff.tariff_version == new_version
    assert _bill(state, "300", before, discom).status == "tariff_not_configured"


def test_maharashtra_old_and_new_versions_give_different_official_rates():
    old = _bill("Maharashtra", "100", date(2025, 12, 1), "MSEDCL")
    new = _bill("Maharashtra", "100", date(2026, 6, 1), "MSEDCL")

    assert _component(old, "energy").amount_inr == "428.00"  # 100 x 4.28
    assert _component(new, "energy").amount_inr == "396.00"  # 100 x 3.96


# ------------------------------------------------------------ PM Surya Ghar


def _pmsg(version_suffix):
    return next(r for _, r in INCENTIVES if r.scheme_version.endswith(version_suffix))


def test_pm_surya_ghar_rates_match_the_mnre_guideline():
    standard = _pmsg("STANDARD")
    special = _pmsg("SPECIAL-CATEGORY")

    assert [s["rate_inr_per_kw"] for s in standard.calculation_rules["slabs"]] == [30000, 18000]
    assert standard.maximum_amount == Decimal("78000")
    assert standard.max_system_size_kw == Decimal("3")
    assert [s["rate_inr_per_kw"] for s in special.calculation_rules["slabs"]] == [33000, 19800]
    assert special.maximum_amount is None
    for record in (standard, special):
        assert record.consumer_category == RESIDENTIAL
        assert record.effective_from == date(2024, 2, 13)
        assert record.effective_to == date(2027, 3, 31)


def test_every_state_and_ut_gets_exactly_one_pm_surya_ghar_variant():
    standard = dataset._applicable_regions(_pmsg("STANDARD"))
    special = dataset._applicable_regions(_pmsg("SPECIAL-CATEGORY"))

    assert standard & special == set()
    assert standard | special == set(INDIAN_STATES) | set(INDIAN_UNION_TERRITORIES)
    assert special == {
        "Uttarakhand", "Himachal Pradesh", "Arunachal Pradesh", "Assam", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Sikkim", "Tripura", "Jammu and Kashmir", "Ladakh",
        "Andaman and Nicobar Islands", "Lakshadweep",
    }


# ------------------------------------------------------------ seeding


def _seed_everything(db_session):
    for _, record in DISCOMS:
        seed_discoms.load_discom(db_session, record)
    db_session.flush()
    for _, schedule in TARIFFS:
        seed_tariffs.load_schedule(db_session, schedule)
    for _, record in INCENTIVES:
        seed_incentives.load_scheme(db_session, record)
    db_session.commit()


def _counts(db_session):
    return (
        db_session.query(Discom).count(),
        db_session.query(ElectricityTariff).count(),
        db_session.query(IncentiveProgram).count(),
    )


def test_seeding_creates_the_expected_rows_and_is_idempotent(db_session):
    _seed_everything(db_session)
    first = _counts(db_session)
    _seed_everything(db_session)

    assert first == (5, sum(len(s.slabs) for _, s in TARIFFS), len(INCENTIVES))
    assert _counts(db_session) == first


def test_a_second_seed_run_changes_nothing(db_session):
    _seed_everything(db_session)

    totals = seed_tariffs.SeedStats()
    for _, schedule in TARIFFS:
        totals.add(seed_tariffs.load_schedule(db_session, schedule))

    assert (totals.inserted, totals.updated, totals.deactivated) == (0, 0, 0)
    assert totals.unchanged == sum(len(s.slabs) for _, s in TARIFFS)


def test_no_duplicate_natural_keys_after_seeding(db_session):
    _seed_everything(db_session)

    keys = [
        (r.state, r.discom_id, r.consumer_category, r.tariff_version, Decimal(str(r.slab_min_kwh)))
        for r in db_session.query(ElectricityTariff).all()
    ]
    assert len(keys) == len(set(keys))


def test_seeded_rows_carry_source_metadata_and_are_verified_and_active(db_session):
    _seed_everything(db_session)

    for row in db_session.query(ElectricityTariff).all():
        assert row.verification_status == IncentiveVerificationStatus.VERIFIED and row.active
        assert is_official_source_url(row.source_url)
        assert row.source_page and row.source_order_number and row.source_excerpt and row.last_verified
    for row in db_session.query(IncentiveProgram).all():
        assert row.verification_status == IncentiveVerificationStatus.VERIFIED and row.active
        assert is_official_source_url(row.source_url)
        assert row.source_page and row.source_order_number and row.source_excerpt


def test_a_slab_removed_from_a_schedule_file_is_deactivated_not_deleted(db_session):
    _seed_everything(db_session)
    schedule = copy.deepcopy(next(s for _, s in TARIFFS if s.tariff_version == "TN-TNPDCL-LT-IA-2025.07"))
    schedule.slabs = schedule.slabs[:-1]
    schedule.slabs[-1].slab_max_kwh = None
    before = _counts(db_session)

    stats = seed_tariffs.load_schedule(db_session, schedule)
    db_session.commit()

    assert stats.deactivated == 1
    assert _counts(db_session) == before
    inactive = db_session.query(ElectricityTariff).filter(ElectricityTariff.active.is_(False)).all()
    assert len(inactive) == 1 and Decimal(str(inactive[0].slab_min_kwh)) == Decimal("500")


def test_a_tariff_row_that_is_not_verified_is_never_used_for_a_bill(client, valid_payload, db_session):
    _seed_everything(db_session)
    for row in db_session.query(ElectricityTariff).filter(ElectricityTariff.state == "Tamil Nadu"):
        row.verification_status = IncentiveVerificationStatus.PENDING_REVIEW
    db_session.commit()
    _locate(db_session, "Tamil Nadu")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    body = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]}).json()

    assert body["status"] == "tariff_not_configured"
    assert body["estimated_monthly_bill_inr"] is None


# --------------------------------------------------------------- end to end


def _locate(db_session, state):
    candidate = GeocodingCandidate(
        latitude=1.0, longitude=2.0, formatted_address=f"TEST {state}", city="TEST", state=state, country="India"
    )
    service = make_test_location_service(
        geocoding_provider=FakeGeocodingProvider(reverse_result=candidate),
        india_resolver=IndiaLocationResolver(discom_repository=DiscomRepository(db_session)),
    )
    app.dependency_overrides[get_location_service] = lambda: service


def _assessment(client, valid_payload, state, building_type="home", kwh=950):
    payload = copy.deepcopy(valid_payload)
    payload["building"]["building_type"] = building_type
    payload["location"]["state"] = state
    payload["energy"]["monthly_consumption_kwh"] = kwh
    return client.post("/api/v1/assessments", json=payload).json()["id"]


def _calculate(client, assessment_id):
    return client.post("/api/v1/tariffs/calculate", json={"assessment_id": assessment_id}).json()


def _evaluate(client, assessment_id, capacity=3):
    return client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": assessment_id, "technology": "solar", "proposed_capacity_kw": capacity},
    ).json()


def test_chennai_home_gets_the_tnpdcl_tariff_with_its_source(client, valid_payload, db_session):
    _seed_everything(db_session)
    _locate(db_session, "Tamil Nadu")
    body = _calculate(client, _assessment(client, valid_payload, "Tamil Nadu"))

    assert body["status"] == "ok"
    assert body["location"]["discom_status"] == "identified"
    assert "Tamil Nadu Power Distribution" in body["location"]["discom_name"]
    assert body["consumer_category"] == "residential"
    assert body["estimated_monthly_bill_inr"] == "9330.00"
    tariff = body["tariff"]
    assert tariff["tariff_version"] == "TN-TNPDCL-LT-IA-2025.07"
    assert tariff["verification_status"] == "verified"
    assert tariff["source_name"].startswith("Tamil Nadu Electricity Regulatory Commission")
    assert tariff["source_url"].startswith("https://www.tnerc.tn.gov.in/")
    assert tariff["source_order_number"] == "Suo-motu Order No. 6 of 2025"
    assert tariff["source_page"].startswith("34")
    assert tariff["effective_from"] == "2025-07-01"
    assert "subsidy" in tariff["verification_notes"]


def test_chennai_home_gets_pm_surya_ghar_cfa(client, valid_payload, db_session):
    _seed_everything(db_session)
    _locate(db_session, "Tamil Nadu")
    body = _evaluate(client, _assessment(client, valid_payload, "Tamil Nadu"))

    assert body["summary"]["eligible_programmes"] == 1
    [programme] = body["programmes"]
    assert programme["status"] == "eligible"
    assert programme["incentive_amount_inr"] == "78000.00"
    assert programme["source"]["source_url"].startswith("https://cdnbbsr.s3waas.gov.in/")
    assert programme["source"]["verification_status"] == "verified"
    assert programme["scheme_version"] == "PMSG-CFA-2024.02-STANDARD"


@pytest.mark.parametrize("capacity, expected", [(1, "30000.00"), (2, "60000.00"), (2.5, "69000.00"), (6, "78000.00")])
def test_pm_surya_ghar_amounts_match_the_guideline_examples(client, valid_payload, db_session, capacity, expected):
    _seed_everything(db_session)
    _locate(db_session, "Tamil Nadu")

    body = _evaluate(client, _assessment(client, valid_payload, "Tamil Nadu"), capacity)

    assert body["programmes"][0]["incentive_amount_inr"] == expected


def test_a_college_in_chennai_never_receives_the_residential_pm_surya_ghar_cfa(client, valid_payload, db_session):
    _seed_everything(db_session)
    _locate(db_session, "Tamil Nadu")
    assessment_id = _assessment(client, valid_payload, "Tamil Nadu", building_type="college")

    incentives = _evaluate(client, assessment_id)
    tariff = _calculate(client, assessment_id)

    assert incentives["consumer_category"] == "educational_institution"
    [programme] = incentives["programmes"]
    assert programme["status"] == "not_eligible" and programme["incentive_amount_inr"] is None
    assert tariff["status"] == "tariff_not_configured"
    assert tariff["estimated_monthly_bill_inr"] is None


def test_a_special_category_state_gets_the_higher_cfa_and_only_that_variant(client, valid_payload, db_session):
    _seed_everything(db_session)
    _locate(db_session, "Sikkim")

    body = _evaluate(client, _assessment(client, valid_payload, "Sikkim"))

    [programme] = body["programmes"]
    assert programme["scheme_version"] == "PMSG-CFA-2024.02-SPECIAL-CATEGORY"
    assert programme["incentive_amount_inr"] == "85800.00"  # 2 x 33,000 + 1 x 19,800


def test_pm_surya_ghar_is_expired_after_its_implementation_period(client, valid_payload, db_session):
    _seed_everything(db_session)
    _locate(db_session, "Tamil Nadu")
    assessment_id = _assessment(client, valid_payload, "Tamil Nadu")

    body = client.post(
        "/api/v1/incentives/evaluate",
        json={
            "assessment_id": assessment_id,
            "technology": "solar",
            "proposed_capacity_kw": 3,
            "calculation_date": "2027-04-01",
        },
    ).json()

    assert body["programmes"][0]["status"] == "scheme_expired"
    assert body["programmes"][0]["incentive_amount_inr"] is None


def test_maharashtra_is_reported_as_discom_ambiguous_never_guessed(client, valid_payload, db_session):
    _seed_everything(db_session)
    _locate(db_session, "Maharashtra")

    body = _calculate(client, _assessment(client, valid_payload, "Maharashtra"))

    assert body["status"] == "discom_ambiguous"
    assert body["estimated_monthly_bill_inr"] is None


def test_karnataka_and_rajasthan_use_their_state_level_tariffs(client, valid_payload, db_session):
    _seed_everything(db_session)

    _locate(db_session, "Karnataka")
    karnataka = _calculate(client, _assessment(client, valid_payload, "Karnataka"))
    _locate(db_session, "Rajasthan")
    rajasthan = _calculate(client, _assessment(client, valid_payload, "Rajasthan"))

    assert karnataka["status"] == "ok" and karnataka["tariff"]["tariff_version"] == "KA-ESCOMS-LT1-FY2026-27"
    assert karnataka["estimated_monthly_bill_inr"] == "5510.00"
    assert karnataka["is_partial_estimate"] is True
    assert rajasthan["status"] == "ok" and rajasthan["tariff"]["tariff_version"] == "RJ-DISCOMS-LT1-FY2026-27"
    assert rajasthan["estimated_monthly_bill_inr"] == "7462.50"  # 6662.50 energy + 800 fixed


def test_a_state_with_no_verified_tariff_stays_unconfigured_never_zero(client, valid_payload, db_session):
    _seed_everything(db_session)
    for state in ("Kerala", "Gujarat", "Bihar"):
        _locate(db_session, state)
        body = _calculate(client, _assessment(client, valid_payload, state))
        assert body["status"] == "tariff_not_configured"
        assert body["estimated_monthly_bill_inr"] is None
        assert body["charges"] == []


def test_the_seed_lock_is_a_harmless_no_op_outside_postgres(db_session):
    from scripts._seed_common import lock_for_seeding

    lock_for_seeding(db_session)  # SQLite: nothing to lock, must not raise
    _seed_everything(db_session)
    assert _counts(db_session)[0] == 5
