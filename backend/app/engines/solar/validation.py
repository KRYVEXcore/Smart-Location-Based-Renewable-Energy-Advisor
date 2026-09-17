"""Input validation for the Solar Engine.

Every check here returns a plain, human-readable reason string on failure
so the API/response layer can surface it as `insufficient_data` — the
engine never silently substitutes a default or a zero for missing/invalid
data.
"""

from app.engines.solar.assumptions import SUPPORTED_SOLAR_RESOURCE_UNIT
from app.schemas.location import SolarResourceProfile


def validate_consumption(monthly_consumption_kwh: float) -> str | None:
    """Returns a failure reason, or None if valid."""
    if monthly_consumption_kwh <= 0:
        return f"Invalid monthly consumption: {monthly_consumption_kwh} kWh (must be greater than 0)."
    return None


def validate_capacity(capacity_kw: float) -> str | None:
    if capacity_kw <= 0:
        return f"Invalid candidate capacity: {capacity_kw} kW (must be greater than 0)."
    return None


def validate_solar_resource(solar_resource: SolarResourceProfile | None) -> str | None:
    if solar_resource is None:
        return "Solar resource data is unavailable for this location."
    if solar_resource.annual_value is None:
        return "Solar resource data was retrieved but has no usable annual value."
    if solar_resource.annual_value <= 0:
        return f"Solar resource annual value is non-positive ({solar_resource.annual_value})."
    if solar_resource.unit != SUPPORTED_SOLAR_RESOURCE_UNIT:
        return (
            f"Unsupported solar resource unit {solar_resource.unit!r}; "
            f"this engine only interprets {SUPPORTED_SOLAR_RESOURCE_UNIT!r}."
        )
    return None
