"""Elevation via the Open-Elevation public API. Free and keyless.
https://open-elevation.com/
"""

from datetime import UTC, datetime

import httpx

from app.schemas.location import ElevationProfile
from app.services.location.providers.errors import (
    ProviderError,
    ProviderInvalidResponseError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)

BASE_URL = "https://api.open-elevation.com/api/v1/lookup"


class OpenElevationProvider:
    name = "open_elevation"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    def get_elevation(self, latitude: float, longitude: float) -> ElevationProfile:
        try:
            response = httpx.get(
                BASE_URL, params={"locations": f"{latitude},{longitude}"}, timeout=self._timeout
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Open-Elevation request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Open-Elevation request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderRateLimitedError("Open-Elevation rate limit exceeded")
        if response.status_code >= 400:
            raise ProviderError(f"Open-Elevation returned status {response.status_code}")

        try:
            elevation = response.json()["results"][0]["elevation"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderInvalidResponseError("Unexpected Open-Elevation response shape") from exc

        return ElevationProfile(elevation_m=elevation, source="Open-Elevation", retrieved_at=datetime.now(UTC))
