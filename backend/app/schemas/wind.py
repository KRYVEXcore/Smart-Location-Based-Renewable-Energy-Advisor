import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.location import WindResourceProfile
from app.schemas.solar import SolarAssumptionOut

WindCandidateStatus = Literal["technically_feasible", "marginal", "insufficient_resource"]
WindCalculationStatus = Literal["ok", "wind_resource_unavailable", "location_unavailable", "insufficient_data"]


class WindEngineInput(BaseModel):
    """Plain input to the Wind Engine, built by WindCalculationService from
    an Assessment + the Phase 3 LocationProfile. The engine never touches
    the database, FastAPI or a provider.
    """

    wind_resource: WindResourceProfile | None = None
    roof_area_sqft: float | None = None
    land_area_sqft: float | None = None


class WindCandidate(BaseModel):
    capacity_kw: float
    annual_generation_kwh: float
    monthly_generation_kwh: dict[str, float] | None = None
    # Net of the explicit availability and electrical-loss assumptions.
    net_capacity_factor: float
    equivalent_full_load_hours: float
    technical_status: WindCandidateStatus
    technical_notes: list[str] = Field(default_factory=list)


class WindReadingOut(BaseModel):
    reference_height_m: float
    annual_value: float | None = None
    monthly_values: dict[str, float] | None = None
    unit: str


class WindResourceOut(BaseModel):
    """Phase 3 wind-resource metadata, passed through unchanged, plus which
    reading the engine actually used.
    """

    provider: str
    period_represented: str | None = None
    retrieved_at: datetime
    data_type: str
    readings: list[WindReadingOut]
    used_reference_height_m: float
    used_annual_mean_speed_mps: float
    used_monthly_means: bool


class WindTurbineOut(BaseModel):
    name: str
    cut_in_speed_mps: float
    rated_speed_mps: float
    cut_out_speed_mps: float
    power_curve: list[tuple[float, float]]


class WindLocationSummary(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    union_territory: str | None = None
    country: str | None = None


class WindCalculationResponse(BaseModel):
    """Technical wind screening only.

    Never contains a recommendation, cost, subsidy, saving or payback
    figure — those belong to later phases.
    """

    status: WindCalculationStatus
    reason: str | None = None
    assessment_id: uuid.UUID | None = None

    location: WindLocationSummary | None = None
    technology: Literal["wind"] = "wind"
    resource: WindResourceOut | None = None
    turbine_model: WindTurbineOut | None = None
    candidates: list[WindCandidate] = Field(default_factory=list)
    site_space_note: str | None = None

    assumptions: list[SolarAssumptionOut] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    methodology: str | None = None

    calculation_version: str
    assumption_version: str
    calculated_at: datetime


class WindCalculateRequest(BaseModel):
    assessment_id: uuid.UUID
