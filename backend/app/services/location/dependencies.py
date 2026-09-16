"""FastAPI wiring for LocationService.

Kept separate from location_service.py so the service itself has no
dependency on FastAPI and can be unit-tested directly with injected mocks.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.connection import get_db
from app.database.repositories.discom_repository import DiscomRepository
from app.database.repositories.location_resource_snapshot_repository import (
    LocationResourceSnapshotRepository,
)
from app.services.location.cache import InMemoryLocationCache, LocationCache
from app.services.location.india_resolver import IndiaLocationResolver
from app.services.location.location_service import LocationService
from app.services.location.provider_factory import (
    get_elevation_provider,
    get_geocoding_provider,
    get_solar_provider,
    get_weather_provider,
    get_wind_provider,
)

# One process-wide cache instance. A per-request instance would never
# actually cache anything across requests.
_location_cache = InMemoryLocationCache()


def get_location_cache() -> LocationCache:
    return _location_cache


def get_location_service(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    cache: Annotated[LocationCache, Depends(get_location_cache)],
) -> LocationService:
    return LocationService(
        geocoding_provider=get_geocoding_provider(settings),
        solar_provider=get_solar_provider(settings),
        wind_provider=get_wind_provider(settings),
        weather_provider=get_weather_provider(settings),
        elevation_provider=get_elevation_provider(settings),
        cache=cache,
        cache_ttl_seconds=settings.location_cache_ttl_seconds,
        snapshot_repository=LocationResourceSnapshotRepository(db),
        india_resolver=IndiaLocationResolver(discom_repository=DiscomRepository(db)),
    )
