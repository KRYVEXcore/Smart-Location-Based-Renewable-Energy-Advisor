import copy

import pytest


def test_create_assessment(client, valid_payload):
    response = client.post("/api/v1/assessments", json=valid_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "submitted"
    assert body["building"]["building_type"] == "home"
    assert body["building"]["name"] == "My Home"
    assert body["location"]["city"] == "Chennai"
    assert body["energy"]["monthly_consumption_kwh"] == 950
    assert body["constraints"]["roof_area_sqft"] == 2500
    assert body["constraints"]["backup_required"] is True
    assert body["created_at"] == body["updated_at"]


def test_retrieve_assessment(client, valid_payload):
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.get(f"/api/v1/assessments/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["energy"]["monthly_consumption_kwh"] == 950


def test_retrieve_nonexistent_assessment_returns_404(client):
    response = client.get("/api/v1/assessments/00000000-0000-0000-0000-000000009999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Assessment not found"}


def test_update_assessment(client, valid_payload):
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.put(
        f"/api/v1/assessments/{created['id']}",
        json={"energy": {"monthly_consumption_kwh": 1200}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["energy"]["monthly_consumption_kwh"] == 1200
    # Unrelated nested sections are untouched by a partial update.
    assert body["building"]["building_type"] == "home"
    assert body["updated_at"] != body["created_at"]


def test_update_nonexistent_assessment_returns_404(client):
    response = client.put(
        "/api/v1/assessments/00000000-0000-0000-0000-000000009999",
        json={"energy": {"monthly_consumption_kwh": 100}},
    )

    assert response.status_code == 404


def test_delete_assessment(client, valid_payload):
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    delete_response = client.delete(f"/api/v1/assessments/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/assessments/{created['id']}")
    assert get_response.status_code == 404


def test_list_assessments(client, valid_payload):
    client.post("/api/v1/assessments", json=valid_payload)
    other = copy.deepcopy(valid_payload)
    other["building"]["building_type"] = "office"
    client.post("/api/v1/assessments", json=other)

    response = client.get("/api/v1/assessments")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {item["building"]["building_type"] for item in body} == {"home", "office"}


def test_invalid_latitude_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["location"]["latitude"] = 200

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_invalid_longitude_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["location"]["longitude"] = -200

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_zero_consumption_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["energy"]["monthly_consumption_kwh"] = 0

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_absurd_consumption_upper_bound_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["energy"]["monthly_consumption_kwh"] = 999_999_999

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_negative_roof_area_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["constraints"]["roof_area_sqft"] = -10

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_negative_budget_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["constraints"]["budget_inr"] = -1

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_college_building_type_is_accepted(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["building"]["building_type"] = "college"

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 201
    assert response.json()["building"]["building_type"] == "college"


def test_invalid_building_type_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["building"]["building_type"] = "castle"

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_nullable_constraints_are_accepted(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["constraints"] = {"backup_required": False}

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["constraints"]["roof_area_sqft"] is None
    assert body["constraints"]["land_area_sqft"] is None
    assert body["constraints"]["budget_inr"] is None


@pytest.mark.parametrize(
    "constraints",
    [
        # A. all fields filled
        {"roof_area_sqft": 333, "land_area_sqft": 3, "budget_inr": 3_333_333, "backup_required": False},
        # B. all optional fields empty/omitted
        {"backup_required": False},
        # C. only roof area
        {"roof_area_sqft": 333, "backup_required": False},
        # D. only land area
        {"land_area_sqft": 3, "backup_required": False},
        # E. only budget
        {"budget_inr": 3_333_333, "backup_required": False},
        # F. only backup power (explicitly true this time)
        {"backup_required": True},
        # G. roof + budget
        {"roof_area_sqft": 333, "budget_inr": 3_333_333, "backup_required": False},
        # H. land + budget
        {"land_area_sqft": 3, "budget_inr": 3_333_333, "backup_required": False},
        # I. roof + land, no budget
        {"roof_area_sqft": 333, "land_area_sqft": 3, "backup_required": False},
    ],
    ids=["all-filled", "all-empty", "roof-only", "land-only", "budget-only", "backup-only", "roof-budget", "land-budget", "roof-land"],
)
def test_every_optional_constraints_combination_saves_successfully(client, valid_payload, constraints):
    # The wizard's own copy says "All optional — skip anything you're
    # unsure of." — this must actually be true for every combination.
    payload = copy.deepcopy(valid_payload)
    payload["constraints"] = constraints

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 201, response.json()
    body = response.json()["constraints"]
    assert body["roof_area_sqft"] == constraints.get("roof_area_sqft")
    assert body["land_area_sqft"] == constraints.get("land_area_sqft")
    assert body["budget_inr"] == constraints.get("budget_inr")
    assert body["backup_required"] == constraints["backup_required"]


def test_land_area_may_be_smaller_than_roof_area(client, valid_payload):
    # These are different physical resources — no land >= roof rule exists
    # or should be invented.
    payload = copy.deepcopy(valid_payload)
    payload["constraints"] = {"roof_area_sqft": 2000, "land_area_sqft": 50, "backup_required": False}

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 201
    body = response.json()["constraints"]
    assert body["roof_area_sqft"] == 2000
    assert body["land_area_sqft"] == 50


def test_missing_location_object_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    del payload["location"]

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_missing_building_type_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    del payload["building"]["building_type"]

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_missing_consumption_is_rejected(client, valid_payload):
    payload = copy.deepcopy(valid_payload)
    del payload["energy"]["monthly_consumption_kwh"]

    response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 422


def test_repeated_submissions_of_the_same_payload_each_create_a_distinct_assessment(client, valid_payload):
    # There is no idempotency key in this API — each POST is a new
    # assessment by design. Duplicate-submission prevention is a frontend
    # concern (disabling the submit button while a request is in flight).
    first = client.post("/api/v1/assessments", json=valid_payload)
    second = client.post("/api/v1/assessments", json=valid_payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
