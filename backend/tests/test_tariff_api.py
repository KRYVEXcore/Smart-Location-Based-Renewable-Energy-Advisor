import copy
import uuid
from datetime import date

from sqlalchemy import select

from app.database.repositories.discom_repository import DiscomRepository
from app.main import app
from app.models.discom import Discom
from app.models.electricity_tariff import ElectricityTariff
from app.models.enums import TariffConsumerCategory
from app.models.tariff_calculation_snapshot import TariffCalculationSnapshot
from app.schemas.location import GeocodingCandidate
from app.services.location.dependencies import get_location_service
from app.services.location.india_resolver import IndiaLocationResolver
from tests.location_fakes import FakeGeocodingProvider, make_test_location_service


def _override_location_service(db_session, *, state=None, union_territory=None, **overrides):
    candidate = GeocodingCandidate(
        latitude=1.0,
        longitude=2.0,
        formatted_address="TEST location",
        city="TEST City",
        state=state,
        country="India",
    )
    service = make_test_location_service(
        geocoding_provider=FakeGeocodingProvider(reverse_result=candidate),
        india_resolver=IndiaLocationResolver(discom_repository=DiscomRepository(db_session)),
        **overrides,
    )
    app.dependency_overrides[get_location_service] = lambda: service


def _seed_tariff(db_session, **overrides) -> ElectricityTariff:
    defaults = dict(
        state="Tamil Nadu",
        union_territory=None,
        discom_id=None,
        consumer_category=TariffConsumerCategory.RESIDENTIAL,
        tariff_version="TEST-TN-2026.1",
        tariff_name="TEST Domestic Tariff",
        slab_min_kwh=0,
        slab_max_kwh=None,
        energy_charge_inr_per_kwh=5.0,
        fixed_charge_inr=None,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        active=True,
    )
    defaults.update(overrides)
    tariff = ElectricityTariff(**defaults)
    db_session.add(tariff)
    db_session.commit()
    return tariff


def test_calculate_tariff_ok_with_state_level_tariff(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_tariff(db_session, state="Tamil Nadu", energy_charge_inr_per_kwh=5.0)
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["consumer_category"] == "residential"
    assert body["tariff"]["tariff_version"] == "TEST-TN-2026.1"
    # 950 kWh (valid_payload) * 5.00 = 4750.00
    assert body["estimated_monthly_bill_inr"] == "4750.00"
    energy = next(c for c in body["charges"] if c["component"] == "energy")
    assert energy["amount_inr"] == "4750.00"
    for forbidden in ("subsidy", "savings", "payback", "cost"):
        assert forbidden not in body


def test_calculate_tariff_prefers_discom_specific_tariff_when_identified(client, valid_payload, db_session):
    discom = Discom(name="TEST-DISCOM Maharashtra", short_code="TEST-MH", state="Maharashtra")
    db_session.add(discom)
    db_session.commit()
    _override_location_service(db_session, state="Maharashtra")
    _seed_tariff(db_session, state="Maharashtra", discom_id=None, tariff_version="STATE-LEVEL", energy_charge_inr_per_kwh=4.0)
    _seed_tariff(db_session, state="Maharashtra", discom_id=discom.id, tariff_version="DISCOM-LEVEL", energy_charge_inr_per_kwh=9.0)

    payload = copy.deepcopy(valid_payload)
    created = client.post("/api/v1/assessments", json=payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    body = response.json()
    assert body["status"] == "ok"
    assert body["tariff"]["tariff_version"] == "DISCOM-LEVEL"
    assert body["estimated_monthly_bill_inr"] == "8550.00"


def test_calculate_tariff_discom_ambiguous_without_state_level_fallback(client, valid_payload, db_session):
    discom_a = Discom(name="TEST-DISCOM A", state="Karnataka")
    discom_b = Discom(name="TEST-DISCOM B", state="Karnataka")
    db_session.add_all([discom_a, discom_b])
    db_session.commit()
    _override_location_service(db_session, state="Karnataka")
    _seed_tariff(db_session, state="Karnataka", discom_id=discom_a.id, tariff_version="A-ONLY")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "discom_ambiguous"
    assert body["tariff"] is None


def test_calculate_tariff_ambiguous_discom_falls_back_to_state_level_tariff(client, valid_payload, db_session):
    discom_a = Discom(name="TEST-DISCOM A2", state="Karnataka")
    discom_b = Discom(name="TEST-DISCOM B2", state="Karnataka")
    db_session.add_all([discom_a, discom_b])
    db_session.commit()
    _override_location_service(db_session, state="Karnataka")
    _seed_tariff(db_session, state="Karnataka", discom_id=None, tariff_version="STATE-FALLBACK", energy_charge_inr_per_kwh=6.0)
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    body = response.json()
    assert body["status"] == "ok"
    assert body["tariff"]["tariff_version"] == "STATE-FALLBACK"


def test_calculate_tariff_not_configured_for_state_without_any_tariff(client, valid_payload, db_session):
    _override_location_service(db_session, state="Rajasthan")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "tariff_not_configured"
    assert body["reason"]


def test_calculate_tariff_insufficient_data_without_coordinates(client, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    payload = {
        "building": {"building_type": "home"},
        "location": {},
        "energy": {"monthly_consumption_kwh": 300},
        "constraints": {"backup_required": False},
    }
    created = client.post("/api/v1/assessments", json=payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"


def test_calculate_tariff_insufficient_data_when_state_not_resolved(client, valid_payload, db_session):
    _override_location_service(db_session, state="Not A Real State")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"


def test_calculate_tariff_for_nonexistent_assessment_returns_404(client, db_session):
    _override_location_service(db_session, state="Tamil Nadu")

    response = client.post(
        "/api/v1/tariffs/calculate", json={"assessment_id": "00000000-0000-0000-0000-000000009999"}
    )

    assert response.status_code == 404


def test_calculate_tariff_rejects_malformed_request_body(client, db_session):
    _override_location_service(db_session, state="Tamil Nadu")

    response = client.post("/api/v1/tariffs/calculate", json={})

    assert response.status_code == 422


def test_calculate_tariff_records_a_reproducibility_snapshot(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_tariff(db_session, state="Tamil Nadu")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    stmt = select(TariffCalculationSnapshot).where(
        TariffCalculationSnapshot.assessment_id == uuid.UUID(created["id"])
    )
    snapshots = list(db_session.execute(stmt).scalars())

    assert len(snapshots) == 1
    assert snapshots[0].calculation_version
    assert snapshots[0].input_snapshot["consumer_category"] == "residential"


def test_deleting_assessment_with_tariff_snapshot_still_works(client, valid_payload, db_session):
    # Regression guard for the same FK-cascade class of bug fixed for
    # solar_calculation_snapshots in Phase 4.
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_tariff(db_session, state="Tamil Nadu")
    created = client.post("/api/v1/assessments", json=valid_payload).json()
    client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    response = client.delete(f"/api/v1/assessments/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/v1/assessments/{created['id']}").status_code == 404


def test_calculate_tariff_respects_calculation_date_for_versioning(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_tariff(
        db_session,
        state="Tamil Nadu",
        tariff_version="OLD",
        energy_charge_inr_per_kwh=2.0,
        effective_from=date(2020, 1, 1),
        effective_to=date(2025, 12, 31),
    )
    _seed_tariff(
        db_session,
        state="Tamil Nadu",
        tariff_version="NEW",
        energy_charge_inr_per_kwh=8.0,
        effective_from=date(2026, 1, 1),
        effective_to=None,
    )
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    old_response = client.post(
        "/api/v1/tariffs/calculate",
        json={"assessment_id": created["id"], "calculation_date": "2024-06-01"},
    ).json()
    new_response = client.post(
        "/api/v1/tariffs/calculate",
        json={"assessment_id": created["id"], "calculation_date": "2026-06-01"},
    ).json()

    assert old_response["tariff"]["tariff_version"] == "OLD"
    assert old_response["estimated_monthly_bill_inr"] == "1900.00"
    assert new_response["tariff"]["tariff_version"] == "NEW"
    assert new_response["estimated_monthly_bill_inr"] == "7600.00"


def test_calculate_tariff_school_maps_to_educational_institution_category(client, valid_payload, db_session):
    _override_location_service(db_session, state="Kerala")
    _seed_tariff(
        db_session,
        state="Kerala",
        consumer_category=TariffConsumerCategory.EDUCATIONAL_INSTITUTION,
        tariff_version="EDU",
        energy_charge_inr_per_kwh=6.0,
    )
    school_payload = copy.deepcopy(valid_payload)
    school_payload["building"]["building_type"] = "school"
    created = client.post("/api/v1/assessments", json=school_payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    body = response.json()
    assert body["consumer_category"] == "educational_institution"
    assert body["status"] == "ok"
    assert body["tariff"]["tariff_version"] == "EDU"


def test_calculate_tariff_home_does_not_match_an_educational_institution_only_tariff(
    client, valid_payload, db_session
):
    _override_location_service(db_session, state="Kerala")
    _seed_tariff(
        db_session,
        state="Kerala",
        consumer_category=TariffConsumerCategory.EDUCATIONAL_INSTITUTION,
        tariff_version="EDU-ONLY",
    )
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    assert response.json()["status"] == "tariff_not_configured"


def test_get_tariffs_filtered_by_state(client, db_session):
    _seed_tariff(db_session, state="Tamil Nadu", tariff_version="TN-1")
    _seed_tariff(db_session, state="Kerala", tariff_version="KL-1")

    response = client.get("/api/v1/tariffs", params={"state": "Tamil Nadu"})

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["state"] == "Tamil Nadu"


def test_get_tariffs_filtered_by_consumer_category(client, db_session):
    _seed_tariff(db_session, state="Tamil Nadu", consumer_category=TariffConsumerCategory.RESIDENTIAL, tariff_version="RES")
    _seed_tariff(db_session, state="Tamil Nadu", consumer_category=TariffConsumerCategory.COMMERCIAL, tariff_version="COM")

    response = client.get("/api/v1/tariffs", params={"consumer_category": "commercial"})

    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["consumer_category"] == "commercial"
