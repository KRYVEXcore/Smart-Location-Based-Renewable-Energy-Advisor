import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import BuildingType
from app.schemas.location import SolarResourceProfile

TechnicalStatus = Literal["technically_feasible", "technically_infeasible", "insufficient_data"]


class SolarEngineInput(BaseModel):
    """Plain, framework-agnostic input to the Solar Engine.

    Built by SolarCalculationService from an Assessment + LocationProfile —
    the engine itself never touches the database, FastAPI, or a provider.
    """

    monthly_consumption_kwh: float
    roof_area_sqft: float | None = None
    building_type: BuildingType
    solar_resource: SolarResourceProfile | None = None


class SolarSystemOption(BaseModel):
    capacity_kw: float
    estimated_annual_generation_kwh: float | None = None
    estimated_monthly_generation_kwh: dict[str, float] | None = None
    roof_area_required_sqft: float
    generation_coverage_percent: float | None = None
    technical_status: TechnicalStatus
    technical_notes: list[str] = Field(default_factory=list)


class SolarAssumptionOut(BaseModel):
    name: str
    value: float
    unit: str
    source: str
    version: str
    effective_from: str
    notes: str = ""


class SolarDataSource(BaseModel):
    category: Literal["solar_resource", "location"]
    provider: str
    unit: str | None = None
    period_represented: str | None = None
    retrieved_at: datetime | None = None


class SolarLocationSummary(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    union_territory: str | None = None
    country: str | None = None
    discom_status: Literal["identified", "not_identified", "ambiguous"] = "not_identified"


class SolarCalculationResponse(BaseModel):
    """Technical solar system options only.

    Never contains a recommendation, subsidy, tariff, cost, saving, or
    payback figure — those belong to later phases (see the README's Phase 4
    boundary notes).
    """

    status: Literal["ok", "insufficient_data"]
    reason: str | None = None

    location: SolarLocationSummary | None = None
    consumer_category: BuildingType | None = None
    technology: Literal["solar"] = "solar"

    annual_consumption_kwh: float | None = None
    options: list[SolarSystemOption] = Field(default_factory=list)

    assumptions: list[SolarAssumptionOut] = Field(default_factory=list)
    data_sources: list[SolarDataSource] = Field(default_factory=list)

    calculation_version: str
    assumption_version: str
    calculated_at: datetime


class SolarCalculateRequest(BaseModel):
    assessment_id: uuid.UUID
