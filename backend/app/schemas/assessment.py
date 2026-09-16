import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssessmentStatus, BuildingType


class BuildingInput(BaseModel):
    building_type: BuildingType
    name: str | None = Field(default=None, max_length=255)


class LocationInput(BaseModel):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    formatted_address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)


class EnergyProfileInput(BaseModel):
    # 1 electricity unit = 1 kWh.
    monthly_consumption_kwh: float = Field(gt=0, le=500_000)


class BuildingConstraintsInput(BaseModel):
    roof_area_sqft: float | None = Field(default=None, ge=0)
    land_area_sqft: float | None = Field(default=None, ge=0)
    budget_inr: float | None = Field(default=None, ge=0)
    backup_required: bool = False


class AssessmentCreate(BaseModel):
    building: BuildingInput
    location: LocationInput
    energy: EnergyProfileInput
    constraints: BuildingConstraintsInput


class AssessmentUpdate(BaseModel):
    building: BuildingInput | None = None
    location: LocationInput | None = None
    energy: EnergyProfileInput | None = None
    constraints: BuildingConstraintsInput | None = None
    status: AssessmentStatus | None = None


class BuildingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    building_type: BuildingType
    name: str | None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    latitude: float | None
    longitude: float | None
    formatted_address: str | None
    city: str | None
    state: str | None
    country: str | None
    postal_code: str | None


class EnergyProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monthly_consumption_kwh: float
    annual_consumption_kwh: float | None


class BuildingConstraintsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    roof_area_sqft: float | None
    land_area_sqft: float | None
    budget_inr: float | None
    backup_required: bool


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: AssessmentStatus
    created_at: datetime
    updated_at: datetime
    building: BuildingRead
    location: LocationRead
    energy: EnergyProfileRead
    constraints: BuildingConstraintsRead
