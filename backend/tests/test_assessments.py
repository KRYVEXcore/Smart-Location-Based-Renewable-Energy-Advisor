import copy


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
