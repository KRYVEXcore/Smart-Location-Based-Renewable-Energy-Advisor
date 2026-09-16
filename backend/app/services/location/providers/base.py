"""Provider interfaces (Protocols).

Every concrete provider (Nominatim, NASA POWER, Open-Elevation, or a future
commercial replacement) implements one of these. LocationService and the
calculation engines in later phases depend only on these interfaces and the
normalized schemas — never on a specific provider's API shape.
"""

from typing import Protocol

from app.schemas.location import (
    ElevationProfile,
    GeocodingCandidate,
    SolarResourceProfile,
    WeatherProfile,
    WindResourceProfile,
)


class GeocodingProvider(Protocol):
    name: str

    def search(self, query: str, limit: int = 5) -> list[GeocodingCandidate]: ...

    def reverse(self, latitude: float, longitude: float) -> GeocodingCandidate | None: ...


class SolarResourceProviderProtocol(Protocol):
    name: str

    def get_solar_resource(self, latitude: float, longitude: float) -> SolarResourceProfile: ...


class WindResourceProviderProtocol(Protocol):
    name: str

    def get_wind_resource(self, latitude: float, longitude: float) -> WindResourceProfile: ...


class WeatherProviderProtocol(Protocol):
    name: str

    def get_weather(self, latitude: float, longitude: float) -> WeatherProfile: ...


class ElevationProviderProtocol(Protocol):
    name: str

    def get_elevation(self, latitude: float, longitude: float) -> ElevationProfile: ...
