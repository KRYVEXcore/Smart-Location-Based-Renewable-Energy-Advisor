from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.location import GeocodingCandidate, LocationProfile
from app.services.location.dependencies import get_location_service
from app.services.location.location_service import LocationService
from app.services.location.providers.errors import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderNotConfiguredError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)

router = APIRouter()

ServiceDep = Annotated[LocationService, Depends(get_location_service)]

_ERROR_STATUS_CODES = {
    ProviderNotConfiguredError: status.HTTP_501_NOT_IMPLEMENTED,
    ProviderTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
    ProviderRateLimitedError: status.HTTP_429_TOO_MANY_REQUESTS,
    ProviderAuthenticationError: status.HTTP_502_BAD_GATEWAY,
}


def _raise_for_provider_error(exc: ProviderError) -> None:
    status_code = _ERROR_STATUS_CODES.get(type(exc), status.HTTP_502_BAD_GATEWAY)
    raise HTTPException(status_code=status_code, detail=exc.message) from exc


@router.get(
    "/locations/search",
    response_model=list[GeocodingCandidate],
    summary="Search for a place by name (geocoding)",
)
def search_locations(
    service: ServiceDep,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> list[GeocodingCandidate]:
    try:
        return service.search(q, limit=limit)
    except ProviderError as exc:
        _raise_for_provider_error(exc)
        raise  # unreachable, satisfies type checkers


@router.get(
    "/locations/profile",
    response_model=LocationProfile,
    summary="Normalized location intelligence (solar, wind, weather, elevation) for a coordinate",
)
def get_location_profile(
    service: ServiceDep,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
) -> LocationProfile:
    # Individual resource failures degrade gracefully into `errors` inside
    # the profile itself (see LocationService) — this endpoint only raises
    # for failures that would prevent any response at all.
    return service.get_profile(latitude, longitude)
