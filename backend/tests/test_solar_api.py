import uuid

from sqlalchemy import select

from app.main import app
from app.models.solar_calculation_snapshot import SolarCalculationSnapshot
from app.services.location.dependencies import get_location_service
from app.services.location.providers.errors import ProviderTimeoutError
from tests.location_fakes import FakeSolarProvider, make_test_location_service


def _override_location_service(**overrides):
    app.dependency_overrides[get_location_service] = lambda: make_test_location_service(**overrides)


def test_calculate_solar_for_valid_assessment(client, valid_payload):
    _override_location_service()
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/solar/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert len(body["options"]) == 10
    assert body["location"] is not None
    assert body["consumer_category"] == "home"
    assert body["technology"] == "solar"
    # None of these belong in Phase 4.
    assert "subsidy" not in body
    assert "payback" not in body
    assert "cost" not in body
    assert "recommendation" not in body


def test_calculate_solar_for_nonexistent_assessment_returns_404(client):
    _override_location_service()

    response = client.post(
        "/api/v1/solar/calculate", json={"assessment_id": "00000000-0000-0000-0000-000000009999"}
    )

    assert response.status_code == 404


def test_calculate_solar_with_missing_solar_resource_is_insufficient_data(client, valid_payload):
    _override_location_service(solar_provider=FakeSolarProvider(error=ProviderTimeoutError("timed out")))
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post("/api/v1/solar/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["reason"]
    assert body["options"] == []


def test_calculate_solar_rejects_malformed_request_body(client):
    _override_location_service()

    response = client.post("/api/v1/solar/calculate", json={})

    assert response.status_code == 422


def test_calculate_solar_without_coordinates_is_insufficient_data(client):
    _override_location_service()
    payload = {
        "building": {"building_type": "home"},
        "location": {},
        "energy": {"monthly_consumption_kwh": 300},
        "constraints": {"backup_required": False},
    }
    created = client.post("/api/v1/assessments", json=payload).json()

    response = client.post("/api/v1/solar/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"


def test_calculate_solar_records_a_reproducibility_snapshot(client, valid_payload, db_session):
    _override_location_service()
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    client.post("/api/v1/solar/calculate", json={"assessment_id": created["id"]})

    stmt = select(SolarCalculationSnapshot).where(
        SolarCalculationSnapshot.assessment_id == uuid.UUID(created["id"])
    )
    snapshots = list(db_session.execute(stmt).scalars())

    assert len(snapshots) == 1
    assert snapshots[0].calculation_version
    assert snapshots[0].assumption_version
    assert snapshots[0].input_snapshot["monthly_consumption_kwh"] == 950


def test_calculate_solar_college_building_type(client, valid_payload):
    import copy

    _override_location_service()
    payload = copy.deepcopy(valid_payload)
    payload["building"]["building_type"] = "college"
    created = client.post("/api/v1/assessments", json=payload).json()

    response = client.post("/api/v1/solar/calculate", json={"assessment_id": created["id"]})

    assert response.status_code == 200
    assert response.json()["consumer_category"] == "college"


def test_deleting_an_assessment_with_a_solar_snapshot_still_works(client, valid_payload):
    # Regression test: the solar_calculation_snapshots FK must cascade on
    # delete, or Phase 2's DELETE /assessments/{id} breaks for any
    # assessment that has ever had a solar calculation run against it.
    _override_location_service()
    created = client.post("/api/v1/assessments", json=valid_payload).json()
    client.post("/api/v1/solar/calculate", json={"assessment_id": created["id"]})

    response = client.delete(f"/api/v1/assessments/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/v1/assessments/{created['id']}").status_code == 404
