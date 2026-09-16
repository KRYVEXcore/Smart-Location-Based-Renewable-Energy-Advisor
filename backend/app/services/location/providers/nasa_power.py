"""Solar, wind, and weather resource data via the NASA POWER climatology API.

Free and keyless. Returns a 20-year (2001-2020) monthly and annual
climatology for a point. https://power.larc.nasa.gov/docs/services/api/

Solar, wind, and weather are exposed as three separate provider classes
(matching the three separate interfaces in providers/base.py) even though
they share one HTTP endpoint — each is independently swappable for a
different provider later without touching the other two.
"""

from datetime import UTC, datetime
from typing import Any

import httpx

from app.schemas.location import SolarResourceProfile, WeatherProfile, WindResourceProfile, WindSpeedReading
from app.services.location.providers.errors import (
    ProviderError,
    ProviderInvalidResponseError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)

BASE_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
FILL_VALUE = -999.0
MONTH_KEYS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
PERIOD_REPRESENTED = "2001-2020 monthly/annual climatology"
SOURCE_NAME = "NASA POWER"


def _fetch_climatology(
    parameters: list[str], latitude: float, longitude: float, timeout_seconds: float
) -> dict[str, Any]:
    try:
        response = httpx.get(
            BASE_URL,
            params={
                "parameters": ",".join(parameters),
                "community": "RE",
                "longitude": longitude,
                "latitude": latitude,
                "format": "JSON",
            },
            timeout=timeout_seconds,
        )
    except httpx.TimeoutException as exc:
        raise ProviderTimeoutError("NASA POWER request timed out") from exc
    except httpx.HTTPError as exc:
        raise ProviderError(f"NASA POWER request failed: {exc}") from exc

    if response.status_code == 429:
        raise ProviderRateLimitedError("NASA POWER rate limit exceeded")
    if response.status_code >= 400:
        raise ProviderError(f"NASA POWER returned status {response.status_code}")

    try:
        data = response.json()
        return data["properties"]["parameter"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ProviderInvalidResponseError("Unexpected NASA POWER response shape") from exc


def _monthly_and_annual(parameter_data: dict[str, float]) -> tuple[dict[str, float] | None, float | None]:
    monthly = {
        month: parameter_data[month]
        for month in MONTH_KEYS
        if parameter_data.get(month) is not None and parameter_data[month] != FILL_VALUE
    }
    annual = parameter_data.get("ANN")
    if annual == FILL_VALUE:
        annual = None
    return (monthly or None, annual)


class NasaPowerSolarProvider:
    name = "nasa_power"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    def get_solar_resource(self, latitude: float, longitude: float) -> SolarResourceProfile:
        parameters = _fetch_climatology(["ALLSKY_SFC_SW_DWN"], latitude, longitude, self._timeout)
        monthly, annual = _monthly_and_annual(parameters.get("ALLSKY_SFC_SW_DWN", {}))
        return SolarResourceProfile(
            annual_value=annual,
            monthly_values=monthly,
            unit="kWh/m^2/day",
            source=SOURCE_NAME,
            period_represented=PERIOD_REPRESENTED,
            retrieved_at=datetime.now(UTC),
        )


class NasaPowerWindProvider:
    name = "nasa_power"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    def get_wind_resource(self, latitude: float, longitude: float) -> WindResourceProfile:
        parameters = _fetch_climatology(["WS10M", "WS50M"], latitude, longitude, self._timeout)
        readings = []
        for key, height_m in (("WS10M", 10.0), ("WS50M", 50.0)):
            monthly, annual = _monthly_and_annual(parameters.get(key, {}))
            readings.append(
                WindSpeedReading(
                    reference_height_m=height_m, annual_value=annual, monthly_values=monthly, unit="m/s"
                )
            )
        return WindResourceProfile(
            readings=readings,
            source=SOURCE_NAME,
            period_represented=PERIOD_REPRESENTED,
            retrieved_at=datetime.now(UTC),
        )


class NasaPowerWeatherProvider:
    name = "nasa_power"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self._timeout = timeout_seconds

    def get_weather(self, latitude: float, longitude: float) -> WeatherProfile:
        parameters = _fetch_climatology(
            ["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "CLRSKY_SFC_SW_DWN"],
            latitude,
            longitude,
            self._timeout,
        )
        monthly_temp, annual_temp = _monthly_and_annual(parameters.get("T2M", {}))
        monthly_precip, annual_precip = _monthly_and_annual(parameters.get("PRECTOTCORR", {}))
        _, annual_allsky = _monthly_and_annual(parameters.get("ALLSKY_SFC_SW_DWN", {}))
        _, annual_clrsky = _monthly_and_annual(parameters.get("CLRSKY_SFC_SW_DWN", {}))

        cloud_index = None
        if annual_allsky is not None and annual_clrsky:
            cloud_index = round(annual_allsky / annual_clrsky, 3)

        return WeatherProfile(
            annual_temperature_c=annual_temp,
            monthly_temperature_c=monthly_temp,
            annual_precipitation_mm_per_day=annual_precip,
            monthly_precipitation_mm_per_day=monthly_precip,
            cloud_index=cloud_index,
            source=SOURCE_NAME,
            period_represented=PERIOD_REPRESENTED,
            retrieved_at=datetime.now(UTC),
        )
