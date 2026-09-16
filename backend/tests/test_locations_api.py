from app.main import app
from app.schemas.location import GeocodingCandidate
from app.services.location.providers.errors import ProviderTimeoutError
from tests.location_fakes import FakeGeocodingProvider, FakeWindProvider, make_test_location_service


def _override_location_service(**overrides):
    from app.services.location.dependencies import get_location_service

    app.dependency_overrides[get_location_service] = lambda: make_test_location_service(**overrides)


def test_search_endpoint_returns_candidates(client):
    _override_location_service()

    response = client.get("/api/v1/locations/search?q=Test")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["formatted_address"] == "Test Place"


def test_search_endpoint_requires_query_param(client):
    _override_location_service()

    response = client.get("/api/v1/locations/search")

    assert response.status_code == 422


def test_profile_endpoint_returns_normalized_profile(client):
    _override_location_service()

    response = client.get("/api/v1/locations/profile?latitude=1.0&longitude=2.0")

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Test City"
    assert body["solar"]["annual_value"] == 5.5
    assert body["wind"]["readings"][0]["reference_height_m"] == 10.0
    assert body["errors"] == {}


def test_profile_endpoint_includes_india_context_with_unrecognized_state(client):
    _override_location_service()

    response = client.get("/api/v1/locations/profile?latitude=1.0&longitude=2.0")

    body = response.json()
    assert body["india"]["state"] is None
    assert body["india"]["discom_status"] == "not_identified"


def test_profile_endpoint_normalizes_real_indian_state(client):
    _override_location_service(
        geocoding_provider=FakeGeocodingProvider(
            reverse_result=GeocodingCandidate(
                latitude=13.08,
                longitude=80.27,
                formatted_address="Chennai, Tamil Nadu, India",
                city="Chennai",
                state="tamil nadu",
                country="India",
            )
        )
    )

    response = client.get("/api/v1/locations/profile?latitude=13.08&longitude=80.27")

    body = response.json()
    assert body["india"]["state"] == "Tamil Nadu"
    assert body["india"]["union_territory"] is None


def test_profile_endpoint_reports_partial_failure(client):
    _override_location_service(wind_provider=FakeWindProvider(error=ProviderTimeoutError("timed out")))

    response = client.get("/api/v1/locations/profile?latitude=1.0&longitude=2.0")

    assert response.status_code == 200
    body = response.json()
    assert body["wind"] is None
    assert body["errors"]["wind"]["code"] == "timeout"
    assert body["solar"] is not None


def test_profile_endpoint_rejects_invalid_latitude(client):
    _override_location_service()

    response = client.get("/api/v1/locations/profile?latitude=200&longitude=80")

    assert response.status_code == 422


def test_profile_endpoint_rejects_invalid_longitude(client):
    _override_location_service()

    response = client.get("/api/v1/locations/profile?latitude=10&longitude=-200")

    assert response.status_code == 422


def test_profile_endpoint_requires_both_coordinates(client):
    _override_location_service()

    response = client.get("/api/v1/locations/profile?latitude=10")

    assert response.status_code == 422
