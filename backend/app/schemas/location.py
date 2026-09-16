from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GeocodingCandidate(BaseModel):
    """A single normalized geocoding/reverse-geocoding result."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    formatted_address: str
    city: str | None = None
    district: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None


class ResourceError(BaseModel):
    """Reported in place of a resource section that could not be retrieved.

    A section with an error is always None in the response — never a
    zero or invented value.
    """

    code: str
    message: str


class SolarResourceProfile(BaseModel):
    annual_value: float | None = None
    monthly_values: dict[str, float] | None = None
    unit: str
    source: str
    period_represented: str | None = None
    retrieved_at: datetime


class WindSpeedReading(BaseModel):
    reference_height_m: float
    annual_value: float | None = None
    monthly_values: dict[str, float] | None = None
    unit: str


class WindResourceProfile(BaseModel):
    readings: list[WindSpeedReading]
    source: str
    period_represented: str | None = None
    retrieved_at: datetime


class WeatherProfile(BaseModel):
    annual_temperature_c: float | None = None
    monthly_temperature_c: dict[str, float] | None = None
    annual_precipitation_mm_per_day: float | None = None
    monthly_precipitation_mm_per_day: dict[str, float] | None = None
    # Ratio of all-sky to clear-sky irradiance (0-1, lower = cloudier).
    # A derived, real metric from the provider's own fields — never invented.
    cloud_index: float | None = None
    source: str
    period_represented: str | None = None
    retrieved_at: datetime


class ElevationProfile(BaseModel):
    elevation_m: float | None = None
    source: str
    retrieved_at: datetime


class DiscomInfo(BaseModel):
    """A resolved electricity distribution company. Only ever populated from
    app.models.discom rows — never guessed.
    """

    id: str
    name: str
    short_code: str | None = None


class IndiaLocationContext(BaseModel):
    """Administrative resolution of a coordinate within India, for future
    tariff/incentive matching. Any field the resolver could not determine
    is None — never a guessed value.

    `state`/`union_territory` are normalized to the canonical spelling in
    app.core.india_geography (exactly one is populated when either is
    known). `discom` is None whenever zero or more than one DISCOM row
    matches — see app.services.location.india_resolver.
    """

    state: str | None = None
    union_territory: str | None = None
    district: str | None = None
    city: str | None = None
    discom: DiscomInfo | None = None
    discom_status: Literal["identified", "not_identified", "ambiguous"] = "not_identified"


class LocationProfile(BaseModel):
    """Normalized location intelligence for a single coordinate.

    Every populated section names its source and retrieval time. A section
    that could not be retrieved is None, with the reason in `errors`.
    """

    latitude: float
    longitude: float
    formatted_address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None

    solar: SolarResourceProfile | None = None
    wind: WindResourceProfile | None = None
    weather: WeatherProfile | None = None
    elevation: ElevationProfile | None = None
    india: IndiaLocationContext | None = None

    errors: dict[str, ResourceError] = Field(default_factory=dict)
    retrieved_at: datetime
