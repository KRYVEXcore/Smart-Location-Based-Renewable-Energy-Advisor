"""Fake provider implementations used only by tests.

These are never imported by app.services.location.provider_factory, so the
production path can never select a mock/fake as if it were a real provider.
"""

from datetime import UTC, datetime

from app.schemas.location import (
    ElevationProfile,
    GeocodingCandidate,
    SolarResourceProfile,
    WeatherProfile,
    WindResourceProfile,
    WindSpeedReading,
)
from app.services.location.cache import InMemoryLocationCache
from app.services.location.location_service import LocationService


class FakeGeocodingProvider:
    name = "fake"

    def __init__(self, reverse_result=None, reverse_error=None, search_results=None):
        self._reverse_result = reverse_result
        self._reverse_error = reverse_error
        self._search_results = search_results if search_results is not None else [
            GeocodingCandidate(latitude=1.0, longitude=2.0, formatted_address="Test Place")
        ]
        self.search_call_count = 0
        self.reverse_call_count = 0

    def search(self, query: str, limit: int = 5) -> list[GeocodingCandidate]:
        self.search_call_count += 1
        return self._search_results

    def reverse(self, latitude: float, longitude: float) -> GeocodingCandidate | None:
        self.reverse_call_count += 1
        if self._reverse_error:
            raise self._reverse_error
        return self._reverse_result


class _FakeResourceProvider:
    """Shared plumbing for the four single-method fake resource providers below."""

    name = "fake"

    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error
        self.call_count = 0

    def _fetch(self):
        self.call_count += 1
        if self._error:
            raise self._error
        return self._result


class FakeSolarProvider(_FakeResourceProvider):
    def get_solar_resource(self, latitude: float, longitude: float):
        return self._fetch()


class FakeWindProvider(_FakeResourceProvider):
    def get_wind_resource(self, latitude: float, longitude: float):
        return self._fetch()


class FakeWeatherProvider(_FakeResourceProvider):
    def get_weather(self, latitude: float, longitude: float):
        return self._fetch()


class FakeElevationProvider(_FakeResourceProvider):
    def get_elevation(self, latitude: float, longitude: float):
        return self._fetch()


def default_solar_profile() -> SolarResourceProfile:
    return SolarResourceProfile(
        annual_value=5.5,
        monthly_values={"JAN": 5.0},
        unit="kWh/m^2/day",
        source="fake",
        retrieved_at=datetime.now(UTC),
    )


def default_wind_profile() -> WindResourceProfile:
    return WindResourceProfile(
        readings=[WindSpeedReading(reference_height_m=10.0, annual_value=4.0, unit="m/s")],
        source="fake",
        retrieved_at=datetime.now(UTC),
    )


def default_weather_profile() -> WeatherProfile:
    return WeatherProfile(annual_temperature_c=28.0, source="fake", retrieved_at=datetime.now(UTC))


def default_elevation_profile() -> ElevationProfile:
    return ElevationProfile(elevation_m=42.0, source="fake", retrieved_at=datetime.now(UTC))


def default_geocoding_candidate() -> GeocodingCandidate:
    return GeocodingCandidate(
        latitude=1.0,
        longitude=2.0,
        formatted_address="Test Place, Test State, Test Country",
        city="Test City",
        state="Test State",
        country="Test Country",
    )


def make_test_location_service(**overrides) -> LocationService:
    defaults = {
        "geocoding_provider": FakeGeocodingProvider(reverse_result=default_geocoding_candidate()),
        "solar_provider": FakeSolarProvider(result=default_solar_profile()),
        "wind_provider": FakeWindProvider(result=default_wind_profile()),
        "weather_provider": FakeWeatherProvider(result=default_weather_profile()),
        "elevation_provider": FakeElevationProvider(result=default_elevation_profile()),
        "cache": InMemoryLocationCache(),
        "cache_ttl_seconds": 60,
        "snapshot_repository": None,
    }
    defaults.update(overrides)
    return LocationService(**defaults)
