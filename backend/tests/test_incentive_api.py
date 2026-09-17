import copy
import uuid
from datetime import date

from sqlalchemy import select

from app.database.repositories.discom_repository import DiscomRepository
from app.main import app
from app.models.discom import Discom
from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)
from app.models.incentive_evaluation_snapshot import IncentiveEvaluationSnapshot
from app.models.incentive_program import IncentiveProgram
from app.schemas.location import GeocodingCandidate
from app.services.location.dependencies import get_location_service
from app.services.location.india_resolver import IndiaLocationResolver
from tests.location_fakes import FakeGeocodingProvider, make_test_location_service


def _override_location_service(db_session, *, state=None, **overrides):
    candidate = GeocodingCandidate(
        latitude=1.0, longitude=2.0, formatted_address="TEST location", city="TEST City", state=state, country="India"
    )
    service = make_test_location_service(
        geocoding_provider=FakeGeocodingProvider(reverse_result=candidate),
        india_resolver=IndiaLocationResolver(discom_repository=DiscomRepository(db_session)),
        **overrides,
    )
    app.dependency_overrides[get_location_service] = lambda: service


def _seed_incentive(db_session, **overrides) -> IncentiveProgram:
    defaults = dict(
        scheme_name="TEST FIXTURE ONLY — Central Scheme",
        scheme_version="TEST-CENTRAL-2026.1",
        level=IncentiveLevel.CENTRAL,
        incentive_type=IncentiveType.CAPITAL_SUBSIDY,
        state=None,
        union_territory=None,
        discom_id=None,
        consumer_category=TariffConsumerCategory.RESIDENTIAL,
        technology=RenewableTechnology.SOLAR,
        subsidy_type=SubsidyType.FIXED_AMOUNT,
        subsidy_value=15000,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        verification_status=IncentiveVerificationStatus.VERIFIED,
        active=True,
    )
    defaults.update(overrides)
    incentive = IncentiveProgram(**defaults)
    db_session.add(incentive)
    db_session.commit()
    return incentive


def test_evaluate_central_scheme_ok_for_residential_solar(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session)
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert len(body["programmes"]) == 1
    programme = body["programmes"][0]
    assert programme["status"] == "eligible"
    assert programme["incentive_amount_inr"] == "15000.00"
    assert body["summary"]["eligible_programmes"] == 1
    for forbidden in ("final_cost", "savings", "payback", "roi"):
        assert forbidden not in body


def test_evaluate_non_residential_rejected_for_residential_only_central_scheme(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session)
    payload = copy.deepcopy(valid_payload)
    payload["building"]["building_type"] = "office"
    created = client.post("/api/v1/assessments", json=payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    body = response.json()
    assert body["consumer_category"] == "commercial"
    assert body["programmes"][0]["status"] == "not_eligible"
    assert body["programmes"][0]["eligible"] is False


def test_evaluate_state_scheme_ok(client, valid_payload, db_session):
    _override_location_service(db_session, state="Karnataka")
    _seed_incentive(db_session, level=IncentiveLevel.STATE, incentive_type=IncentiveType.STATE_SUBSIDY, state="Karnataka", scheme_name="TEST FIXTURE ONLY — State Scheme")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    body = response.json()
    assert body["programmes"][0]["status"] == "eligible"
    assert body["programmes"][0]["level"] == "state"


def test_evaluate_discom_specific_scheme_when_identified(client, valid_payload, db_session):
    discom = Discom(name="TEST-DISCOM Maharashtra", short_code="TEST-MH", state="Maharashtra")
    db_session.add(discom)
    db_session.commit()
    _override_location_service(db_session, state="Maharashtra")
    _seed_incentive(
        db_session,
        level=IncentiveLevel.DISCOM,
        incentive_type=IncentiveType.DISCOM_INCENTIVE,
        state="Maharashtra",
        discom_id=discom.id,
        scheme_name="TEST FIXTURE ONLY — DISCOM Scheme",
    )
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    body = response.json()
    assert len(body["programmes"]) == 1
    assert body["programmes"][0]["status"] == "eligible"
    assert body["programmes"][0]["level"] == "discom"


def test_evaluate_discom_ambiguous_blocks_discom_scheme(client, valid_payload, db_session):
    db_session.add_all(
        [Discom(name="TEST-DISCOM A", state="Karnataka"), Discom(name="TEST-DISCOM B", state="Karnataka")]
    )
    db_session.commit()
    discom_a = db_session.query(Discom).filter_by(name="TEST-DISCOM A").one()
    _override_location_service(db_session, state="Karnataka")
    _seed_incentive(
        db_session,
        level=IncentiveLevel.DISCOM,
        incentive_type=IncentiveType.DISCOM_INCENTIVE,
        state="Karnataka",
        discom_id=discom_a.id,
        scheme_name="TEST FIXTURE ONLY — Ambiguous DISCOM Scheme",
    )
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    body = response.json()
    assert len(body["programmes"]) == 1
    assert body["programmes"][0]["status"] == "discom_ambiguous"
    assert body["programmes"][0]["eligible"] is False


def test_evaluate_state_without_any_configured_incentive_returns_no_programmes_found(client, valid_payload, db_session):
    _override_location_service(db_session, state="Rajasthan")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    body = response.json()
    assert body["status"] == "ok"
    assert body["programmes"] == []
    assert body["summary"]["calculation_status"] == "no_programmes_found"


def test_evaluate_expired_scheme_reported_as_expired(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session, effective_from=date(2020, 1, 1), effective_to=date(2021, 12, 31))
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={
            "assessment_id": created["id"],
            "technology": "solar",
            "proposed_capacity_kw": 3,
            "calculation_date": "2026-06-01",
        },
    )

    body = response.json()
    assert body["programmes"][0]["status"] == "scheme_expired"


def test_evaluate_wind_scheme(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session, technology=RenewableTechnology.WIND, scheme_name="TEST FIXTURE ONLY — Wind Scheme")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "wind", "proposed_capacity_kw": 3},
    )

    body = response.json()
    assert body["programmes"][0]["status"] == "eligible"
    assert body["programmes"][0]["technology"] == "wind"


def test_evaluate_hybrid_scheme(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session, technology=RenewableTechnology.HYBRID, scheme_name="TEST FIXTURE ONLY — Hybrid Scheme")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "hybrid", "proposed_capacity_kw": 3},
    )

    assert response.json()["programmes"][0]["status"] == "eligible"


def test_evaluate_battery_scheme(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session, technology=RenewableTechnology.BATTERY, scheme_name="TEST FIXTURE ONLY — Battery Scheme")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "battery", "proposed_capacity_kw": 3},
    )

    assert response.json()["programmes"][0]["status"] == "eligible"


def test_evaluate_solar_scheme_does_not_apply_to_wind_request(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session, technology=RenewableTechnology.SOLAR)
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "wind", "proposed_capacity_kw": 3},
    )

    # The solar-only scheme is never returned for a wind request at all
    # (the repository filters by requested technology).
    assert response.json()["programmes"] == []


def test_evaluate_insufficient_data_without_coordinates(client, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    payload = {
        "building": {"building_type": "home"},
        "location": {},
        "energy": {"monthly_consumption_kwh": 300},
        "constraints": {"backup_required": False},
    }
    created = client.post("/api/v1/assessments", json=payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"


def test_evaluate_insufficient_data_when_state_not_resolved(client, valid_payload, db_session):
    _override_location_service(db_session, state="Not A Real State")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    assert response.json()["status"] == "insufficient_data"


def test_evaluate_for_nonexistent_assessment_returns_404(client, db_session):
    _override_location_service(db_session, state="Tamil Nadu")

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={
            "assessment_id": "00000000-0000-0000-0000-000000009999",
            "technology": "solar",
            "proposed_capacity_kw": 3,
        },
    )

    assert response.status_code == 404


def test_evaluate_rejects_malformed_request_body(client, db_session):
    _override_location_service(db_session, state="Tamil Nadu")

    response = client.post("/api/v1/incentives/evaluate", json={})

    assert response.status_code == 422


def test_evaluate_rejects_zero_capacity(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 0},
    )

    assert response.status_code == 422


def test_evaluate_rejects_negative_capacity(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    response = client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": -3},
    )

    assert response.status_code == 422


def test_evaluate_records_a_reproducibility_snapshot(client, valid_payload, db_session):
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session)
    created = client.post("/api/v1/assessments", json=valid_payload).json()

    client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    stmt = select(IncentiveEvaluationSnapshot).where(
        IncentiveEvaluationSnapshot.assessment_id == uuid.UUID(created["id"])
    )
    snapshots = list(db_session.execute(stmt).scalars())
    assert len(snapshots) == 1
    assert snapshots[0].input_snapshot["technology"] == "solar"


def test_deleting_assessment_with_incentive_snapshot_still_works(client, valid_payload, db_session):
    # Regression guard for the same FK-cascade class of bug fixed for
    # solar_calculation_snapshots (Phase 4) and tariff_calculation_snapshots
    # (Phase 5).
    _override_location_service(db_session, state="Tamil Nadu")
    _seed_incentive(db_session)
    created = client.post("/api/v1/assessments", json=valid_payload).json()
    client.post(
        "/api/v1/incentives/evaluate",
        json={"assessment_id": created["id"], "technology": "solar", "proposed_capacity_kw": 3},
    )

    response = client.delete(f"/api/v1/assessments/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/v1/assessments/{created['id']}").status_code == 404


def test_get_incentives_filtered_by_state(client, db_session):
    _seed_incentive(db_session, level=IncentiveLevel.STATE, incentive_type=IncentiveType.STATE_SUBSIDY, state="Tamil Nadu", scheme_version="TN-1")
    _seed_incentive(db_session, level=IncentiveLevel.STATE, incentive_type=IncentiveType.STATE_SUBSIDY, state="Kerala", scheme_version="KL-1")

    response = client.get("/api/v1/incentives", params={"state": "Tamil Nadu"})

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["state"] == "Tamil Nadu"


def test_get_incentives_filtered_by_technology(client, db_session):
    _seed_incentive(db_session, technology=RenewableTechnology.SOLAR, scheme_version="SOLAR-1")
    _seed_incentive(db_session, technology=RenewableTechnology.WIND, scheme_version="WIND-1")

    response = client.get("/api/v1/incentives", params={"technology": "wind"})

    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["technology"] == "wind"


def test_get_incentives_filtered_by_level(client, db_session):
    _seed_incentive(db_session, level=IncentiveLevel.CENTRAL, scheme_version="C-1")
    _seed_incentive(db_session, level=IncentiveLevel.STATE, incentive_type=IncentiveType.STATE_SUBSIDY, state="Kerala", scheme_version="S-1")

    response = client.get("/api/v1/incentives", params={"level": "state"})

    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["level"] == "state"
