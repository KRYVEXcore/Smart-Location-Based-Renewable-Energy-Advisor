import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import TariffConsumerCategory

ChargeComponentName = Literal["energy", "fixed", "demand", "wheeling", "tod"]
ChargeComponentStatus = Literal["included", "not_included", "not_calculated"]
TariffDataStatus = Literal["ok", "insufficient_data", "tariff_not_configured", "discom_ambiguous"]


class TariffSlabInput(BaseModel):
    """A single tariff slab row, decoupled from the SQLAlchemy model — the
    engine in app.engines.tariff never touches the database directly.
    """

    tariff_version: str
    tariff_name: str
    slab_min_kwh: Decimal
    slab_max_kwh: Decimal | None = None
    energy_charge_inr_per_kwh: Decimal
    fixed_charge_inr: Decimal | None = None
    demand_charge_inr: Decimal | None = None
    wheeling_charge_inr_per_kwh: Decimal | None = None
    effective_from: date
    effective_to: date | None = None
    source_url: str | None = None
    source_document: str | None = None
    source_name: str | None = None
    last_verified: date | None = None
    discom_id: uuid.UUID | None = None


class TariffChargeComponent(BaseModel):
    component: ChargeComponentName
    status: ChargeComponentStatus
    # Rendered as a string (never a float) so Decimal precision survives the
    # JSON boundary exactly as computed.
    amount_inr: str | None = None
    notes: str | None = None


class TariffLocationSummary(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    union_territory: str | None = None
    country: str | None = None
    discom_status: Literal["identified", "not_identified", "ambiguous"] = "not_identified"
    discom_name: str | None = None


class TariffScheduleSummary(BaseModel):
    tariff_name: str
    tariff_version: str
    consumer_category: TariffConsumerCategory
    effective_from: date
    effective_to: date | None = None
    source_url: str | None = None
    source_document: str | None = None
    source_name: str | None = None
    last_verified: date | None = None


class TariffCalculationResponse(BaseModel):
    """An estimated baseline grid-electricity bill only.

    Never contains a subsidy, solar cost, payback, or savings figure — see
    the README's Phase 5 boundary notes. Any charge component this app
    cannot calculate (demand, time-of-day) is reported as
    "not_calculated" rather than omitted or fabricated as zero.
    """

    status: TariffDataStatus
    reason: str | None = None

    location: TariffLocationSummary | None = None
    consumer_category: TariffConsumerCategory | None = None
    tariff: TariffScheduleSummary | None = None

    monthly_consumption_kwh: str | None = None
    charges: list[TariffChargeComponent] = Field(default_factory=list)
    estimated_monthly_bill_inr: str | None = None
    is_partial_estimate: bool = True
    excluded_components: list[str] = Field(default_factory=list)

    calculation_version: str
    calculated_at: datetime


class TariffCalculateRequest(BaseModel):
    assessment_id: uuid.UUID
    # Defaults to today (server-side) when omitted.
    calculation_date: date | None = None


class TariffSlabOut(BaseModel):
    """A raw slab row, for GET /api/v1/tariffs browsing/debugging."""

    id: uuid.UUID
    state: str | None
    union_territory: str | None
    discom_id: uuid.UUID | None
    consumer_category: TariffConsumerCategory
    tariff_version: str
    tariff_name: str
    slab_min_kwh: Decimal
    slab_max_kwh: Decimal | None
    energy_charge_inr_per_kwh: Decimal
    fixed_charge_inr: Decimal | None
    demand_charge_inr: Decimal | None
    wheeling_charge_inr_per_kwh: Decimal | None
    effective_from: date
    effective_to: date | None
    source_url: str | None
    source_document: str | None
    source_name: str | None
    last_verified: date | None
    active: bool

    model_config = {"from_attributes": True}
