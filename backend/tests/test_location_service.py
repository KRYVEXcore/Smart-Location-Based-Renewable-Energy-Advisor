from app.services.location.providers.errors import ProviderTimeoutError
from tests.location_fakes import (
    FakeGeocodingProvider,
    FakeSolarProvider,
    FakeWindProvider,
    default_solar_profile,
    make_test_location_service,
)


def test_get_profile_assembles_all_sections():
    service = make_test_location_service()

    profile = service.get_profile(1.0, 2.0)

    assert profile.city == "Test City"
    assert profile.solar.annual_value == 5.5
    assert profile.wind.readings[0].reference_height_m == 10.0
    assert profile.weather.annual_temperature_c == 28.0
    assert profile.elevation.elevation_m == 42.0
    assert profile.errors == {}


def test_get_profile_degrades_gracefully_when_one_provider_fails():
    service = make_test_location_service(
        wind_provider=FakeWindProvider(error=ProviderTimeoutError("timed out"))
    )

    profile = service.get_profile(1.0, 2.0)

    assert profile.wind is None
    assert profile.errors["wind"].code == "timeout"
    # Other sections are unaffected by the wind provider failing.
    assert profile.solar is not None
    assert profile.elevation is not None


def test_get_profile_reports_geocoding_failure_without_crashing():
    service = make_test_location_service(
        geocoding_provider=FakeGeocodingProvider(reverse_error=ProviderTimeoutError("timed out"))
    )

    profile = service.get_profile(1.0, 2.0)

    assert profile.formatted_address is None
    assert profile.errors["geocoding"].code == "timeout"
    assert profile.solar is not None  # resource sections still succeed


def test_get_profile_caches_successful_fetches():
    solar_provider = FakeSolarProvider(result=default_solar_profile())
    service = make_test_location_service(solar_provider=solar_provider)

    service.get_profile(1.0, 2.0)
    service.get_profile(1.0, 2.0)

    assert solar_provider.call_count == 1


def test_get_profile_does_not_cache_failures():
    wind_provider = FakeWindProvider(error=ProviderTimeoutError("timed out"))
    service = make_test_location_service(wind_provider=wind_provider)

    service.get_profile(1.0, 2.0)
    service.get_profile(1.0, 2.0)

    assert wind_provider.call_count == 2


def test_search_returns_geocoding_candidates():
    service = make_test_location_service()

    results = service.search("Test")

    assert len(results) == 1
    assert results[0].formatted_address == "Test Place"


def test_search_results_are_cached():
    geocoding_provider = FakeGeocodingProvider()
    service = make_test_location_service(geocoding_provider=geocoding_provider)

    service.search("Test")
    service.search("Test")

    assert geocoding_provider.search_call_count == 1
