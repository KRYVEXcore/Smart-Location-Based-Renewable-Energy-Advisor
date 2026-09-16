from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    secret_key: str = "change-me"
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/renewable_energy_advisor"
    )
    cors_allowed_origins: str = "http://localhost:5173"

    # Location intelligence providers (Phase 3). Every provider below has a
    # free, keyless default so the app runs locally with zero configuration.
    # *_api_key vars exist so a commercial provider can be swapped in later
    # (see app/services/location/provider_factory.py) — they are optional.
    geocoding_provider: str = "nominatim"
    geocoding_api_key: str | None = None
    solar_resource_provider: str = "nasa_power"
    solar_resource_api_key: str | None = None
    wind_resource_provider: str = "nasa_power"
    wind_resource_api_key: str | None = None
    weather_provider: str = "nasa_power"
    weather_api_key: str | None = None
    elevation_provider: str = "open_elevation"
    elevation_api_key: str | None = None

    # How long a fetched resource profile is considered fresh enough to
    # reuse from cache, in seconds. Climatology/elevation data changes
    # essentially never — this just avoids hammering free public APIs.
    location_cache_ttl_seconds: int = 86_400
    provider_request_timeout_seconds: float = 10.0

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
