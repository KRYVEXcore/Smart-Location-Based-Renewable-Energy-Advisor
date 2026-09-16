"""Provider normalization and error-handling tests.

No test here makes a real network call — httpx.get is monkeypatched with
canned responses shaped like real (previously verified) provider payloads.
"""

import httpx
import pytest

from app.services.location.providers import nasa_power, nominatim, open_elevation
from app.services.location.providers.errors import (
    ProviderInvalidResponseError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)

NOMINATIM_SEARCH_FIXTURE = [
    {
        "place_id": 249896291,
        "lat": "13.0836939",
        "lon": "80.2701860",
        "display_name": "Chennai Corporation, Chennai, Tamil Nadu, India",
        "address": {
            "city": "Chennai Corporation",
            "state": "Tamil Nadu",
            "country": "India",
            "country_code": "in",
        },
    }
]

NASA_POWER_SOLAR_FIXTURE = {
    "properties": {
        "parameter": {
            "ALLSKY_SFC_SW_DWN": {
                "JAN": 4.9759,
                "FEB": 5.8373,
                "ANN": 5.2224,
            }
        }
    }
}


# --- Nominatim geocoding ---------------------------------------------------


def test_nominatim_search_normalizes_result(monkeypatch):
    def fake_get(url, **kwargs):
        assert "/search" in url
        return httpx.Response(200, json=NOMINATIM_SEARCH_FIXTURE)

    monkeypatch.setattr(nominatim.httpx, "get", fake_get)

    results = nominatim.NominatimGeocodingProvider().search("Chennai")

    assert len(results) == 1
    assert results[0].latitude == pytest.approx(13.0836939)
    assert results[0].city == "Chennai Corporation"
    assert results[0].state == "Tamil Nadu"
    assert results[0].country == "India"


def test_nominatim_reverse_returns_none_on_error_shape(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(200, json={"error": "Unable to geocode"})

    monkeypatch.setattr(nominatim.httpx, "get", fake_get)

    assert nominatim.NominatimGeocodingProvider().reverse(0, 0) is None


def test_nominatim_rate_limit_raises(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(429)

    monkeypatch.setattr(nominatim.httpx, "get", fake_get)

    with pytest.raises(ProviderRateLimitedError):
        nominatim.NominatimGeocodingProvider().search("Chennai")


def test_nominatim_timeout_raises(monkeypatch):
    def fake_get(url, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(nominatim.httpx, "get", fake_get)

    with pytest.raises(ProviderTimeoutError):
        nominatim.NominatimGeocodingProvider().search("Chennai")


# --- NASA POWER (solar / wind / weather) -----------------------------------


def test_nasa_power_solar_normalizes_result(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(200, json=NASA_POWER_SOLAR_FIXTURE)

    monkeypatch.setattr(nasa_power.httpx, "get", fake_get)

    profile = nasa_power.NasaPowerSolarProvider().get_solar_resource(13.08, 80.27)

    assert profile.annual_value == pytest.approx(5.2224)
    assert profile.monthly_values["JAN"] == pytest.approx(4.9759)
    assert profile.unit == "kWh/m^2/day"
    assert profile.source == "NASA POWER"


def test_nasa_power_wind_retains_reference_heights(monkeypatch):
    fixture = {
        "properties": {
            "parameter": {
                "WS10M": {"JAN": 3.71, "ANN": 4.0},
                "WS50M": {"JAN": 4.99, "ANN": 5.29},
            }
        }
    }

    def fake_get(url, **kwargs):
        return httpx.Response(200, json=fixture)

    monkeypatch.setattr(nasa_power.httpx, "get", fake_get)

    profile = nasa_power.NasaPowerWindProvider().get_wind_resource(13.08, 80.27)

    heights = {reading.reference_height_m for reading in profile.readings}
    assert heights == {10.0, 50.0}
    ten_m = next(r for r in profile.readings if r.reference_height_m == 10.0)
    assert ten_m.annual_value == pytest.approx(4.0)


def test_nasa_power_weather_computes_cloud_index(monkeypatch):
    fixture = {
        "properties": {
            "parameter": {
                "T2M": {"ANN": 27.95},
                "PRECTOTCORR": {"ANN": 3.43},
                "ALLSKY_SFC_SW_DWN": {"ANN": 5.2224},
                "CLRSKY_SFC_SW_DWN": {"ANN": 6.3679},
            }
        }
    }

    def fake_get(url, **kwargs):
        return httpx.Response(200, json=fixture)

    monkeypatch.setattr(nasa_power.httpx, "get", fake_get)

    profile = nasa_power.NasaPowerWeatherProvider().get_weather(13.08, 80.27)

    assert profile.annual_temperature_c == pytest.approx(27.95)
    assert profile.annual_precipitation_mm_per_day == pytest.approx(3.43)
    assert profile.cloud_index == pytest.approx(5.2224 / 6.3679, rel=1e-3)


def test_nasa_power_treats_fill_value_as_missing(monkeypatch):
    fixture = {"properties": {"parameter": {"ALLSKY_SFC_SW_DWN": {"JAN": -999.0, "ANN": -999.0}}}}

    def fake_get(url, **kwargs):
        return httpx.Response(200, json=fixture)

    monkeypatch.setattr(nasa_power.httpx, "get", fake_get)

    profile = nasa_power.NasaPowerSolarProvider().get_solar_resource(0, 0)

    assert profile.annual_value is None
    assert profile.monthly_values is None


def test_nasa_power_invalid_response_shape_raises(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(200, json={"unexpected": "shape"})

    monkeypatch.setattr(nasa_power.httpx, "get", fake_get)

    with pytest.raises(ProviderInvalidResponseError):
        nasa_power.NasaPowerSolarProvider().get_solar_resource(0, 0)


def test_nasa_power_timeout_raises(monkeypatch):
    def fake_get(url, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(nasa_power.httpx, "get", fake_get)

    with pytest.raises(ProviderTimeoutError):
        nasa_power.NasaPowerSolarProvider().get_solar_resource(0, 0)


# --- Open-Elevation ---------------------------------------------------------


def test_open_elevation_normalizes_result(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(200, json={"results": [{"latitude": 13.08, "longitude": 80.27, "elevation": 4.0}]})

    monkeypatch.setattr(open_elevation.httpx, "get", fake_get)

    profile = open_elevation.OpenElevationProvider().get_elevation(13.08, 80.27)

    assert profile.elevation_m == 4.0
    assert profile.source == "Open-Elevation"


def test_open_elevation_timeout_raises(monkeypatch):
    def fake_get(url, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(open_elevation.httpx, "get", fake_get)

    with pytest.raises(ProviderTimeoutError):
        open_elevation.OpenElevationProvider().get_elevation(13.08, 80.27)


def test_open_elevation_invalid_response_raises(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(200, json={"unexpected": "shape"})

    monkeypatch.setattr(open_elevation.httpx, "get", fake_get)

    with pytest.raises(ProviderInvalidResponseError):
        open_elevation.OpenElevationProvider().get_elevation(13.08, 80.27)
