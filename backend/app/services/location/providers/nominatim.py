"""Geocoding via the OpenStreetMap Nominatim public API.

Free and keyless. Usage policy requires an identifying User-Agent and asks
callers not to send more than ~1 request/second — LocationService's cache
keeps repeat lookups from hitting this at all.
https://operations.osmfoundation.org/policies/nominatim/
"""

from typing import Any

import httpx

from app.schemas.location import GeocodingCandidate
from app.services.location.providers.errors import (
    ProviderError,
    ProviderInvalidResponseError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)

BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "RenewableEnergyAdvisor-SIH2026/1.0 (educational prototype)"


class NominatimGeocodingProvider:
    name = "nominatim"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    def search(self, query: str, limit: int = 5) -> list[GeocodingCandidate]:
        data = self._request(
            "/search",
            {
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": limit,
                # Scopes results to India per the Phase 3 spec, without
                # hard-coding any specific city or place.
                "countrycodes": "in",
            },
        )
        if not isinstance(data, list):
            raise ProviderInvalidResponseError("Unexpected Nominatim search response shape")
        return [self._to_candidate(item) for item in data]

    def reverse(self, latitude: float, longitude: float) -> GeocodingCandidate | None:
        data = self._request(
            "/reverse", {"lat": latitude, "lon": longitude, "format": "json", "addressdetails": 1}
        )
        if not isinstance(data, dict) or "error" in data:
            return None
        return self._to_candidate(data)

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        try:
            response = httpx.get(
                f"{BASE_URL}{path}",
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Nominatim request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Nominatim request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderRateLimitedError("Nominatim rate limit exceeded")
        if response.status_code >= 400:
            raise ProviderError(f"Nominatim returned status {response.status_code}")

        try:
            return response.json()
        except ValueError as exc:
            raise ProviderInvalidResponseError("Nominatim returned invalid JSON") from exc

    def _to_candidate(self, item: dict[str, Any]) -> GeocodingCandidate:
        address = item.get("address") or {}
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("state_district")
        )
        district = address.get("state_district") or address.get("county")
        return GeocodingCandidate(
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            formatted_address=item.get("display_name", ""),
            city=city,
            district=district,
            state=address.get("state"),
            country=address.get("country"),
            postal_code=address.get("postcode"),
        )
