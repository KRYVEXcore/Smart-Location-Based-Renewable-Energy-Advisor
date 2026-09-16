"""Reads the configured provider name for each resource category and
returns the matching adapter. This is the only place that knows about
concrete provider classes — LocationService only sees the interfaces in
providers/base.py. Adding a new provider means adding one branch here.
"""

from app.core.config import Settings
from app.services.location.providers.base import (
    ElevationProviderProtocol,
    GeocodingProvider,
    SolarResourceProviderProtocol,
    WeatherProviderProtocol,
    WindResourceProviderProtocol,
)
from app.services.location.providers.errors import ProviderNotConfiguredError
from app.services.location.providers.nasa_power import (
    NasaPowerSolarProvider,
    NasaPowerWeatherProvider,
    NasaPowerWindProvider,
)
from app.services.location.providers.nominatim import NominatimGeocodingProvider
from app.services.location.providers.open_elevation import OpenElevationProvider


def get_geocoding_provider(settings: Settings) -> GeocodingProvider:
    if settings.geocoding_provider == "nominatim":
        return NominatimGeocodingProvider(timeout_seconds=settings.provider_request_timeout_seconds)
    raise ProviderNotConfiguredError(f"Unknown geocoding provider: {settings.geocoding_provider!r}")


def get_solar_provider(settings: Settings) -> SolarResourceProviderProtocol:
    if settings.solar_resource_provider == "nasa_power":
        return NasaPowerSolarProvider(timeout_seconds=settings.provider_request_timeout_seconds)
    raise ProviderNotConfiguredError(
        f"Unknown solar resource provider: {settings.solar_resource_provider!r}"
    )


def get_wind_provider(settings: Settings) -> WindResourceProviderProtocol:
    if settings.wind_resource_provider == "nasa_power":
        return NasaPowerWindProvider(timeout_seconds=settings.provider_request_timeout_seconds)
    raise ProviderNotConfiguredError(
        f"Unknown wind resource provider: {settings.wind_resource_provider!r}"
    )


def get_weather_provider(settings: Settings) -> WeatherProviderProtocol:
    if settings.weather_provider == "nasa_power":
        return NasaPowerWeatherProvider(timeout_seconds=settings.provider_request_timeout_seconds)
    raise ProviderNotConfiguredError(f"Unknown weather provider: {settings.weather_provider!r}")


def get_elevation_provider(settings: Settings) -> ElevationProviderProtocol:
    if settings.elevation_provider == "open_elevation":
        return OpenElevationProvider(timeout_seconds=settings.provider_request_timeout_seconds)
    raise ProviderNotConfiguredError(f"Unknown elevation provider: {settings.elevation_provider!r}")
