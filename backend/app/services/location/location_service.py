import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from app.database.repositories.location_resource_snapshot_repository import (
    LocationResourceSnapshotRepository,
)
from app.schemas.location import GeocodingCandidate, LocationProfile, ResourceError
from app.services.location.cache import LocationCache, make_cache_key
from app.services.location.india_resolver import IndiaLocationResolver
from app.services.location.providers.base import (
    ElevationProviderProtocol,
    GeocodingProvider,
    SolarResourceProviderProtocol,
    WeatherProviderProtocol,
    WindResourceProviderProtocol,
)
from app.services.location.providers.errors import ProviderError

logger = logging.getLogger(__name__)

ProfileT = TypeVar("ProfileT")


class LocationService:
    """Orchestrates geocoding and resource providers into a normalized
    LocationProfile. Depends only on the provider interfaces in
    providers/base.py — never on a specific provider's API shape.

    Each resource fetch degrades independently: a failure produces a
    ResourceError entry rather than failing the whole request, so partial
    results (e.g. solar available, wind unavailable) are still useful.
    """

    def __init__(
        self,
        *,
        geocoding_provider: GeocodingProvider,
        solar_provider: SolarResourceProviderProtocol,
        wind_provider: WindResourceProviderProtocol,
        weather_provider: WeatherProviderProtocol,
        elevation_provider: ElevationProviderProtocol,
        cache: LocationCache,
        cache_ttl_seconds: float,
        snapshot_repository: LocationResourceSnapshotRepository | None = None,
        india_resolver: IndiaLocationResolver | None = None,
    ) -> None:
        self._geocoding = geocoding_provider
        self._solar = solar_provider
        self._wind = wind_provider
        self._weather = weather_provider
        self._elevation = elevation_provider
        self._cache = cache
        self._cache_ttl_seconds = cache_ttl_seconds
        self._snapshots = snapshot_repository
        self._india_resolver = india_resolver or IndiaLocationResolver(discom_repository=None)

    def search(self, query: str, limit: int = 5) -> list[GeocodingCandidate]:
        cache_key = make_cache_key("geocode", "search", query.strip().lower(), limit)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        results = self._geocoding.search(query, limit=limit)
        self._cache.set(cache_key, results, self._cache_ttl_seconds)
        return results

    def get_profile(self, latitude: float, longitude: float) -> LocationProfile:
        # Rounding gives nearby lookups (e.g. repeated dashboard views of the
        # same assessment) a real chance of a cache hit.
        lat = round(latitude, 4)
        lon = round(longitude, 4)
        errors: dict[str, ResourceError] = {}

        address = self._safe_reverse_geocode(lat, lon, errors)
        india = self._india_resolver.resolve(address)
        solar = self._fetch_resource("solar", lat, lon, self._solar.get_solar_resource, errors)
        wind = self._fetch_resource("wind", lat, lon, self._wind.get_wind_resource, errors)
        weather = self._fetch_resource("weather", lat, lon, self._weather.get_weather, errors)
        elevation = self._fetch_resource("elevation", lat, lon, self._elevation.get_elevation, errors)

        if self._snapshots is not None:
            try:
                self._snapshots.db.commit()
            except Exception:
                logger.exception("Failed to commit location resource snapshots (best-effort, non-fatal)")

        return LocationProfile(
            latitude=latitude,
            longitude=longitude,
            formatted_address=address.formatted_address if address else None,
            city=address.city if address else None,
            state=address.state if address else None,
            country=address.country if address else None,
            solar=solar,
            wind=wind,
            weather=weather,
            elevation=elevation,
            india=india,
            errors=errors,
            retrieved_at=datetime.now(UTC),
        )

    def _safe_reverse_geocode(
        self, latitude: float, longitude: float, errors: dict[str, ResourceError]
    ) -> GeocodingCandidate | None:
        cache_key = make_cache_key("geocode", "reverse", latitude, longitude)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            result = self._geocoding.reverse(latitude, longitude)
        except ProviderError as exc:
            errors["geocoding"] = ResourceError(code=exc.code, message=exc.message)
            return None

        self._cache.set(cache_key, result, self._cache_ttl_seconds)
        return result

    def _fetch_resource(
        self,
        resource_type: str,
        latitude: float,
        longitude: float,
        fetch_fn: Callable[[float, float], ProfileT],
        errors: dict[str, ResourceError],
    ) -> ProfileT | None:
        cache_key = make_cache_key(resource_type, latitude, longitude)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            profile = fetch_fn(latitude, longitude)
        except ProviderError as exc:
            errors[resource_type] = ResourceError(code=exc.code, message=exc.message)
            return None
        except Exception as exc:  # a provider bug shouldn't take down the whole profile
            logger.exception("Unexpected error fetching %s resource", resource_type)
            errors[resource_type] = ResourceError(code="unavailable", message=str(exc))
            return None

        self._cache.set(cache_key, profile, self._cache_ttl_seconds)
        self._record_snapshot(resource_type, latitude, longitude, profile)
        return profile

    def _record_snapshot(self, resource_type: str, latitude: float, longitude: float, profile: object) -> None:
        if self._snapshots is None:
            return
        try:
            self._snapshots.record(
                latitude=latitude,
                longitude=longitude,
                resource_type=resource_type,
                provider=getattr(profile, "source", resource_type),
                payload=profile.model_dump(mode="json"),  # type: ignore[attr-defined]
                retrieved_at=profile.retrieved_at,  # type: ignore[attr-defined]
            )
        except Exception:
            logger.exception("Failed to record location resource snapshot (best-effort, non-fatal)")
