from functools import lru_cache

from pydantic import field_validator
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

    @field_validator("database_url")
    @classmethod
    def _use_psycopg2_driver(cls, value: str) -> str:
        # Managed hosts (Render, Heroku) hand out plain postgres:// or
        # postgresql:// URLs, which SQLAlchemy would resolve to a driver
        # this project doesn't install.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg2://" + value[len(prefix):]
        return value

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

    # SHREA AI advisor (Phase 8). The API key is backend-only: it is never
    # sent to the browser or to the model, and the advisor reports
    # "ai_not_configured" (never a fabricated answer) while it is unset.
    ai_provider: str = "nvidia"
    ai_model: str = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
    ai_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key: str | None = None
    ai_timeout_seconds: float = 30.0
    ai_max_output_tokens: int = 800
    ai_history_limit: int = 6
    ai_rate_limit_per_minute: int = 10
    ai_global_rate_limit_per_minute: int = 30

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
