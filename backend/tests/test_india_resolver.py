from app.database.repositories.discom_repository import DiscomRepository
from app.models.discom import Discom
from app.schemas.location import GeocodingCandidate
from app.services.location.india_resolver import IndiaLocationResolver


def test_resolve_with_no_candidate_returns_all_none():
    resolver = IndiaLocationResolver(discom_repository=None)

    context = resolver.resolve(None)

    assert context.state is None
    assert context.union_territory is None
    assert context.discom is None
    assert context.discom_status == "not_identified"


def test_resolve_normalizes_state_and_leaves_discom_unidentified_without_repository():
    resolver = IndiaLocationResolver(discom_repository=None)
    candidate = GeocodingCandidate(
        latitude=13.08, longitude=80.27, formatted_address="Chennai", state="tamil nadu", city="Chennai"
    )

    context = resolver.resolve(candidate)

    assert context.state == "Tamil Nadu"
    assert context.union_territory is None
    assert context.discom is None
    assert context.discom_status == "not_identified"


def test_resolve_treats_union_territory_correctly():
    resolver = IndiaLocationResolver(discom_repository=None)
    candidate = GeocodingCandidate(latitude=28.6, longitude=77.2, formatted_address="Delhi", state="Delhi")

    context = resolver.resolve(candidate)

    assert context.state is None
    assert context.union_territory == "Delhi"


def test_resolve_leaves_unrecognized_state_as_none_rather_than_guessing():
    resolver = IndiaLocationResolver(discom_repository=None)
    candidate = GeocodingCandidate(
        latitude=1.0, longitude=2.0, formatted_address="Nowhere", state="Not A Real State"
    )

    context = resolver.resolve(candidate)

    assert context.state is None
    assert context.union_territory is None
    assert context.discom_status == "not_identified"


def test_resolve_identifies_discom_when_exactly_one_matches(db_session):
    # Clearly a test fixture — not real DISCOM data.
    db_session.add(Discom(name="TEST-DISCOM Tamil Nadu", short_code="TEST-TNDISC", state="Tamil Nadu"))
    db_session.commit()

    resolver = IndiaLocationResolver(discom_repository=DiscomRepository(db_session))
    candidate = GeocodingCandidate(
        latitude=13.08, longitude=80.27, formatted_address="Chennai", state="Tamil Nadu"
    )

    context = resolver.resolve(candidate)

    assert context.discom_status == "identified"
    assert context.discom is not None
    assert context.discom.name == "TEST-DISCOM Tamil Nadu"


def test_resolve_reports_ambiguous_when_multiple_discoms_match(db_session):
    db_session.add_all(
        [
            Discom(name="TEST-DISCOM A", state="Maharashtra"),
            Discom(name="TEST-DISCOM B", state="Maharashtra"),
        ]
    )
    db_session.commit()

    resolver = IndiaLocationResolver(discom_repository=DiscomRepository(db_session))
    candidate = GeocodingCandidate(
        latitude=19.0, longitude=72.8, formatted_address="Mumbai", state="Maharashtra"
    )

    context = resolver.resolve(candidate)

    assert context.discom is None
    assert context.discom_status == "ambiguous"


def test_resolve_ignores_inactive_discoms(db_session):
    db_session.add(Discom(name="TEST-DISCOM Retired", state="Kerala", is_active=False))
    db_session.commit()

    resolver = IndiaLocationResolver(discom_repository=DiscomRepository(db_session))
    candidate = GeocodingCandidate(latitude=10.0, longitude=76.0, formatted_address="Kochi", state="Kerala")

    context = resolver.resolve(candidate)

    assert context.discom_status == "not_identified"
