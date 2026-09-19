import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


# Sensible ceiling for one month's bill (INR): ten lakh rupees.
MAX_MONTHLY_BILL_INR = 1_000_000


class EnergyProfileInput(BaseModel):
    """The customer's electricity input. The primary input is the average monthly bill (INR).
    Units (kWh) are optional; when given they are the authoritative consumption and the bill
    is kept alongside them. 1 electricity unit = 1 kWh.
    """

    monthly_electricity_bill_inr: float | None = Field(default=None, gt=0, le=MAX_MONTHLY_BILL_INR)
    monthly_consumption_kwh: float | None = Field(default=None, gt=0, le=500_000)

    @model_validator(mode="after")
    def _needs_a_bill_or_units(self) -> "EnergyProfileInput":
        if self.monthly_electricity_bill_inr is None and self.monthly_consumption_kwh is None:
            raise ValueError("Enter your average monthly electricity bill (or the units consumed).")
        return self


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
    monthly_consumption_kwh: float | None
    annual_consumption_kwh: float | None
    monthly_electricity_bill_inr: float | None = None
    # 'user_kwh' = entered by the user; 'user_bill_estimate' = an estimate derived from the bill.
    consumption_source: str = "user_kwh"
    consumption_estimate: dict | None = None


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
