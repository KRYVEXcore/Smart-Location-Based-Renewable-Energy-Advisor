"""POST /api/v1/wind/calculate through the real location pipeline (Phase 3
India resolver + a fake wind PROVIDER). Wind speeds are TEST FIXTURE ONLY
values: live runs against real Phase 3 data are done separately.
"""

import copy
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.database.repositories.discom_repository import DiscomRepository
from app.main import app
from app.models.wind_calculation_snapshot import WindCalculationSnapshot
from app.schemas.location import GeocodingCandidate, WindResourceProfile, WindSpeedReading
from app.services.location.dependencies import get_location_service
from app.services.location.india_resolver import IndiaLocationResolver
from app.services.location.providers.errors import ProviderTimeoutError
from tests.location_fakes import FakeGeocodingProvider, FakeWindProvider, make_test_location_service


def make_fixture_wind(annual=5.0, monthly=None) -> WindResourceProfile:
    """TEST FIXTURE ONLY."""
    return WindResourceProfile(
        readings=[
            WindSpeedReading(reference_height_m=10.0, annual_value=annual, monthly_values=monthly, unit="m/s"),
            WindSpeedReading(reference_height_m=50.0, annual_value=None if annual is None else annual + 1.2, unit="m/s"),
        ],
        source="TEST FIXTURE ONLY",
        period_represented="2001-2020 monthly/annual climatology",
        retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _locate(db_session, *, state="Tamil Nadu", country="India", wind=None, wind_error=None):
    candidate = GeocodingCandidate(
        latitude=1.0, longitude=2.0, formatted_address=f"TEST {state}", city="TEST", state=state, country=country
    )
    wind_provider = FakeWindProvider(result=wind or make_fixture_wind(), error=wind_error)
    service = make_test_location_service(
        geocoding_provider=FakeGeocodingProvider(reverse_result=candidate),
        india_resolver=IndiaLocationResolver(discom_repository=DiscomRepository(db_session)),
        wind_provider=wind_provider,
    )
    app.dependency_overrides[get_location_service] = lambda: service


def _calculate(client, payload):
    created = client.post("/api/v1/assessments", json=payload).json()
    return created["id"], client.post("/api/v1/wind/calculate", json={"assessment_id": created["id"]})


def test_calculate_wind_for_an_indian_assessment(client, valid_payload, db_session):
    _locate(db_session)

    assessment_id, response = _calculate(client, valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["assessment_id"] == assessment_id
    assert body["technology"] == "wind"
    assert body["location"]["state"] == "Tamil Nadu"
    assert [c["capacity_kw"] for c in body["candidates"]] == [0.5, 1, 2, 3, 5, 10]
    assert body["resource"]["provider"] == "TEST FIXTURE ONLY"
    assert body["resource"]["used_reference_height_m"] == 10.0
    assert body["assumption_version"] == "wind-assumptions-2026.1"
    assert body["site_space_note"]


def test_the_response_has_no_recommendation_or_financial_fields(client, valid_payload, db_session):
    _locate(db_session)
    _, response = _calculate(client, valid_payload)

    def keys(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key.lower()
                yield from keys(value)
        elif isinstance(node, list):
            for item in node:
                yield from keys(item)

    found = set(keys(response.json()))
    for forbidden in ("recommendation", "recommended", "best", "cost", "subsidy", "savings", "payback", "roi"):
        assert forbidden not in found


@pytest.mark.parametrize(
    "city, state",
    [
        ("Chennai", "Tamil Nadu"),
        ("Bengaluru", "Karnataka"),
        ("Mumbai", "Maharashtra"),
        ("Kochi", "Kerala"),
        ("Jaipur", "Rajasthan"),
    ],
)
def test_indian_cities_flow_through_location_to_the_wind_engine(client, valid_payload, db_session, city, state):
    _locate(db_session, state=state)
    payload = copy.deepcopy(valid_payload)
    payload["location"].update(city=city, state=state)

    _, response = _calculate(client, payload)

    body = response.json()
    assert body["status"] == "ok"
    assert body["location"]["state"] == state
    assert len(body["candidates"]) == 6


def test_wind_resource_unavailable_is_reported_never_defaulted(client, valid_payload, db_session):
    _locate(db_session, wind_error=ProviderTimeoutError("timed out"))

    _, response = _calculate(client, valid_payload)

    body = response.json()
    assert body["status"] == "wind_resource_unavailable"
    assert "No verified wind resource" in body["reason"]
    assert body["candidates"] == [] and body["resource"] is None


def test_wind_data_without_a_usable_annual_value_is_insufficient_data(client, valid_payload, db_session):
    _locate(db_session, wind=make_fixture_wind(annual=None))

    _, response = _calculate(client, valid_payload)

    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["candidates"] == []


def test_a_location_outside_india_is_location_unavailable(client, valid_payload, db_session):
    _locate(db_session, state="California", country="United States")

    _, response = _calculate(client, valid_payload)

    body = response.json()
    assert body["status"] == "location_unavailable"
    assert body["candidates"] == []


def test_an_assessment_without_coordinates_is_location_unavailable(client, valid_payload, db_session):
    _locate(db_session)
    payload = copy.deepcopy(valid_payload)
    payload["location"].update(latitude=None, longitude=None)

    _, response = _calculate(client, payload)

    assert response.json()["status"] == "location_unavailable"


def test_a_nonexistent_assessment_is_404(client, db_session):
    _locate(db_session)

    response = client.post("/api/v1/wind/calculate", json={"assessment_id": "00000000-0000-0000-0000-000000009999"})

    assert response.status_code == 404


@pytest.mark.parametrize("body", [{}, {"assessment_id": "not-a-uuid"}, {"assessment_id": None}])
def test_request_validation_rejects_a_missing_or_malformed_assessment_id(client, db_session, body):
    _locate(db_session)

    assert client.post("/api/v1/wind/calculate", json=body).status_code == 422


def test_roof_and_land_from_the_assessment_reach_the_site_space_note(client, valid_payload, db_session):
    _locate(db_session)
    payload = copy.deepcopy(valid_payload)
    payload["constraints"].update(roof_area_sqft=1500, land_area_sqft=4000)

    _, response = _calculate(client, payload)

    note = response.json()["site_space_note"]
    assert "roof 1,500 sq ft" in note and "land 4,000 sq ft" in note


def test_the_same_assessment_and_resource_always_give_the_same_candidates(client, valid_payload, db_session):
    _locate(db_session)
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    first = client.post("/api/v1/wind/calculate", json={"assessment_id": created["id"]}).json()
    second = client.post("/api/v1/wind/calculate", json={"assessment_id": created["id"]}).json()

    assert first["candidates"] == second["candidates"]


def test_a_calculation_snapshot_is_persisted_with_versions_and_resource_input(client, valid_payload, db_session):
    _locate(db_session)

    assessment_id, _ = _calculate(client, valid_payload)

    snapshots = db_session.execute(select(WindCalculationSnapshot)).scalars().all()
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert str(snapshot.assessment_id) == assessment_id
    assert snapshot.assumption_version == "wind-assumptions-2026.1"
    assert snapshot.calculation_version == "wind-engine-2026.1"
    assert snapshot.input_snapshot["wind_resource"]["source"] == "TEST FIXTURE ONLY"
    assert snapshot.result_snapshot["status"] == "ok"
    assert len(snapshot.result_snapshot["candidates"]) == 6


def test_deleting_an_assessment_is_not_blocked_by_its_wind_snapshot(client, valid_payload, db_session):
    _locate(db_session)
    assessment_id, _ = _calculate(client, valid_payload)

    assert client.delete(f"/api/v1/assessments/{assessment_id}").status_code == 204
    assert db_session.execute(select(WindCalculationSnapshot)).scalars().all() == []


def test_the_wind_endpoint_does_not_disturb_the_solar_and_tariff_endpoints(client, valid_payload, db_session):
    _locate(db_session)
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    client.post("/api/v1/wind/calculate", json={"assessment_id": created["id"]})
    solar = client.post("/api/v1/solar/calculate", json={"assessment_id": created["id"]})
    tariff = client.post("/api/v1/tariffs/calculate", json={"assessment_id": created["id"]})

    assert solar.status_code == 200 and solar.json()["status"] == "ok"
    assert tariff.status_code == 200
