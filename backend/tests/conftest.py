import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """An isolated in-memory SQLite database, never the real dev Postgres DB."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def valid_payload() -> dict:
    return {
        "building": {"building_type": "home", "name": "My Home"},
        "location": {
            "latitude": 13.114,
            "longitude": 80.154,
            "formatted_address": "Chennai, Tamil Nadu, India",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "country": "India",
        },
        "energy": {"monthly_consumption_kwh": 950},
        "constraints": {
            "roof_area_sqft": 2500,
            "land_area_sqft": None,
            "budget_inr": 300000,
            "backup_required": True,
        },
    }
