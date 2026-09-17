from datetime import UTC, datetime

from app.engines.solar.validation import validate_capacity, validate_consumption, validate_solar_resource
from app.schemas.location import SolarResourceProfile


def test_validate_consumption_rejects_zero():
    assert validate_consumption(0) is not None


def test_validate_consumption_rejects_negative():
    assert validate_consumption(-5) is not None


def test_validate_consumption_accepts_positive():
    assert validate_consumption(500) is None


def test_validate_capacity_rejects_zero_and_negative():
    assert validate_capacity(0) is not None
    assert validate_capacity(-1) is not None


def test_validate_capacity_accepts_positive():
    assert validate_capacity(3) is None


def test_validate_solar_resource_rejects_none():
    assert validate_solar_resource(None) is not None


def test_validate_solar_resource_rejects_missing_annual_value():
    resource = SolarResourceProfile(
        annual_value=None, unit="kWh/m^2/day", source="TEST", retrieved_at=datetime.now(UTC)
    )
    assert validate_solar_resource(resource) is not None


def test_validate_solar_resource_rejects_non_positive_value():
    resource = SolarResourceProfile(
        annual_value=0, unit="kWh/m^2/day", source="TEST", retrieved_at=datetime.now(UTC)
    )
    assert validate_solar_resource(resource) is not None


def test_validate_solar_resource_rejects_unsupported_unit():
    resource = SolarResourceProfile(
        annual_value=5.0, unit="W/m^2", source="TEST", retrieved_at=datetime.now(UTC)
    )
    assert validate_solar_resource(resource) is not None


def test_validate_solar_resource_accepts_valid_resource():
    resource = SolarResourceProfile(
        annual_value=5.0, unit="kWh/m^2/day", source="TEST", retrieved_at=datetime.now(UTC)
    )
    assert validate_solar_resource(resource) is None
