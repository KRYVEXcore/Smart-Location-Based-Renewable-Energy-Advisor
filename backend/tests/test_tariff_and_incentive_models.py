"""Schema-level tests for the India tariff/incentive architecture.

These only verify the models can represent the required fields and
relationships — no tariff/incentive calculation engine exists yet (by
design; see app/models/electricity_tariff.py and incentive_program.py).
All records here are clearly-marked test fixtures, never realistic values.
"""

from datetime import date

from app.models.discom import Discom
from app.models.electricity_tariff import ElectricityTariff
from app.models.enums import BuildingType, IncentiveLevel, RenewableTechnology, SubsidyType
from app.models.incentive_program import IncentiveProgram


def test_electricity_tariff_stores_all_required_fields(db_session):
    discom = Discom(name="TEST-DISCOM", short_code="TEST", state="Tamil Nadu")
    db_session.add(discom)
    db_session.flush()

    tariff = ElectricityTariff(
        state="Tamil Nadu",
        discom_id=discom.id,
        consumer_category=BuildingType.HOME,
        tariff_name="TEST Domestic Tariff Slab 1",
        slab_min_kwh=0,
        slab_max_kwh=100,
        energy_charge_inr_per_kwh=3.5,
        fixed_charge_inr=50,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        source_url="https://example.invalid/test-tariff-order",
        source_document="TEST fixture — not a real tariff order",
        last_verified=date(2026, 1, 1),
        active=True,
    )
    db_session.add(tariff)
    db_session.commit()

    fetched = db_session.get(ElectricityTariff, tariff.id)
    assert fetched.state == "Tamil Nadu"
    assert fetched.discom_id == discom.id
    assert fetched.consumer_category == BuildingType.HOME
    assert float(fetched.energy_charge_inr_per_kwh) == 3.5
    assert fetched.effective_to is None
    assert fetched.active is True


def test_electricity_tariff_supports_union_territory_instead_of_state(db_session):
    tariff = ElectricityTariff(
        union_territory="Delhi",
        state=None,
        consumer_category=BuildingType.OFFICE,
        tariff_name="TEST UT Commercial Tariff",
        energy_charge_inr_per_kwh=7.0,
        effective_from=date(2026, 1, 1),
        active=True,
    )
    db_session.add(tariff)
    db_session.commit()

    fetched = db_session.get(ElectricityTariff, tariff.id)
    assert fetched.union_territory == "Delhi"
    assert fetched.state is None


def test_electricity_tariff_college_consumer_category(db_session):
    tariff = ElectricityTariff(
        state="Karnataka",
        consumer_category=BuildingType.COLLEGE,
        tariff_name="TEST College Tariff",
        energy_charge_inr_per_kwh=6.2,
        effective_from=date(2026, 1, 1),
        active=True,
    )
    db_session.add(tariff)
    db_session.commit()

    assert db_session.get(ElectricityTariff, tariff.id).consumer_category == BuildingType.COLLEGE


def test_incentive_program_represents_central_scheme(db_session):
    incentive = IncentiveProgram(
        scheme_name="TEST Central Rooftop Solar Scheme",
        level=IncentiveLevel.CENTRAL,
        state=None,
        union_territory=None,
        consumer_category=BuildingType.HOME,
        technology=RenewableTechnology.SOLAR,
        min_system_size_kw=1,
        max_system_size_kw=3,
        subsidy_type=SubsidyType.PERCENTAGE,
        percentage_value=60,
        maximum_amount=78000,
        eligibility_rules={"note": "TEST fixture — residential rooftop only"},
        effective_from=date(2026, 1, 1),
        effective_to=None,
        source_url="https://example.invalid/test-central-scheme",
        source_document="TEST fixture",
        last_verified=date(2026, 1, 1),
        active=True,
    )
    db_session.add(incentive)
    db_session.commit()

    fetched = db_session.get(IncentiveProgram, incentive.id)
    assert fetched.level == IncentiveLevel.CENTRAL
    assert fetched.state is None
    assert fetched.consumer_category == BuildingType.HOME
    assert float(fetched.percentage_value) == 60


def test_incentive_program_represents_state_scheme(db_session):
    incentive = IncentiveProgram(
        scheme_name="TEST State Solar Incentive",
        level=IncentiveLevel.STATE,
        state="Gujarat",
        technology=RenewableTechnology.SOLAR,
        subsidy_type=SubsidyType.FIXED_AMOUNT,
        subsidy_value=10000,
        effective_from=date(2026, 1, 1),
        active=True,
    )
    db_session.add(incentive)
    db_session.commit()

    assert db_session.get(IncentiveProgram, incentive.id).level == IncentiveLevel.STATE


def test_incentive_program_represents_discom_scheme(db_session):
    discom = Discom(name="TEST-DISCOM-2", state="Maharashtra")
    db_session.add(discom)
    db_session.flush()

    incentive = IncentiveProgram(
        scheme_name="TEST DISCOM Net-Metering Benefit",
        level=IncentiveLevel.DISCOM,
        state="Maharashtra",
        discom_id=discom.id,
        technology=RenewableTechnology.SOLAR,
        subsidy_type=SubsidyType.OTHER,
        effective_from=date(2026, 1, 1),
        active=True,
    )
    db_session.add(incentive)
    db_session.commit()

    fetched = db_session.get(IncentiveProgram, incentive.id)
    assert fetched.level == IncentiveLevel.DISCOM
    assert fetched.discom_id == discom.id


def test_incentive_program_allows_null_consumer_category_for_broad_schemes(db_session):
    incentive = IncentiveProgram(
        scheme_name="TEST Category-Agnostic Scheme",
        level=IncentiveLevel.STATE,
        state="Kerala",
        consumer_category=None,
        technology=RenewableTechnology.HYBRID,
        subsidy_type=SubsidyType.OTHER,
        effective_from=date(2026, 1, 1),
        active=True,
    )
    db_session.add(incentive)
    db_session.commit()

    assert db_session.get(IncentiveProgram, incentive.id).consumer_category is None


def test_incentive_program_can_represent_an_expired_scheme(db_session):
    incentive = IncentiveProgram(
        scheme_name="TEST Expired Scheme",
        level=IncentiveLevel.CENTRAL,
        technology=RenewableTechnology.SOLAR,
        subsidy_type=SubsidyType.PERCENTAGE,
        percentage_value=40,
        effective_from=date(2020, 1, 1),
        effective_to=date(2022, 12, 31),
        active=False,
        last_verified=date(2023, 1, 1),
    )
    db_session.add(incentive)
    db_session.commit()

    fetched = db_session.get(IncentiveProgram, incentive.id)
    assert fetched.active is False
    assert fetched.effective_to == date(2022, 12, 31)


def test_discom_supports_state_and_union_territory_scoping(db_session):
    state_discom = Discom(name="TEST-DISCOM-State", state="Punjab")
    ut_discom = Discom(name="TEST-DISCOM-UT", union_territory="Chandigarh")
    db_session.add_all([state_discom, ut_discom])
    db_session.commit()

    assert db_session.get(Discom, state_discom.id).union_territory is None
    assert db_session.get(Discom, ut_discom.id).state is None
