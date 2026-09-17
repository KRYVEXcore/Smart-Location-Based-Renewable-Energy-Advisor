import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import (
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)

IncentiveEligibilityStatus = Literal[
    "eligible",
    "not_eligible",
    "insufficient_information",
    "scheme_expired",
    "scheme_not_active",
    "scheme_not_verified",
    "incentive_data_unavailable",
    "discom_not_identified",
    "discom_ambiguous",
]
IncentiveEvaluationStatus = Literal["ok", "insufficient_data"]


class IncentiveProgramInput(BaseModel):
    """A single candidate incentive programme row (one scheme version),
    decoupled from the SQLAlchemy model — the engine in
    app.engines.incentive never touches the database directly.
    """

    id: uuid.UUID
    scheme_name: str
    scheme_version: str
    level: IncentiveLevel
    incentive_type: IncentiveType
    technology: RenewableTechnology
    consumer_category: TariffConsumerCategory | None = None

    min_system_size_kw: Decimal | None = None
    max_system_size_kw: Decimal | None = None

    subsidy_type: SubsidyType
    subsidy_value: Decimal | None = None
    percentage_value: Decimal | None = None
    maximum_amount: Decimal | None = None
    calculation_rules: dict | None = None

    eligibility_rules: dict | None = None
    stacking_rules: dict | None = None

    effective_from: date
    effective_to: date | None = None
    verification_status: IncentiveVerificationStatus
    active: bool

    source_name: str | None = None
    source_url: str | None = None
    source_document: str | None = None
    last_verified: date | None = None
    discom_id: uuid.UUID | None = None


class IncentiveSourceInfo(BaseModel):
    source_name: str | None = None
    source_url: str | None = None
    source_document: str | None = None
    last_verified: date | None = None


class IncentiveEligibilityResult(BaseModel):
    """One programme's eligibility outcome. Never hidden or omitted just
    because it's ineligible or unverified — see the API route docstring.
    """

    scheme_name: str
    scheme_version: str | None = None
    level: IncentiveLevel
    incentive_type: IncentiveType | None = None
    technology: RenewableTechnology

    status: IncentiveEligibilityStatus
    eligible: bool
    reason: str | None = None
    missing_fields: list[str] = Field(default_factory=list)

    # Rendered as strings (never floats) so Decimal precision survives the
    # JSON boundary exactly as computed.
    incentive_amount_inr: str | None = None
    eligible_cost_basis_inr: str | None = None
    calculation_notes: str | None = None
    # Set to "combination_requires_verification" when this programme and
    # another eligible one lack documented stacking rules that explicitly
    # allow (or forbid) combining them — see app.engines.incentive.stacking.
    combination_note: str | None = None

    source: IncentiveSourceInfo | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class IncentiveLocationSummary(BaseModel):
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


class IncentiveEvaluationSummary(BaseModel):
    verified_programmes: int = 0
    eligible_programmes: int = 0
    calculation_status: Literal["ok", "insufficient_data", "no_programmes_found"]


class IncentiveEvaluationResponse(BaseModel):
    """Eligibility for verified incentive programmes only.

    Never contains a final solar installation cost, final savings,
    payback, or ROI figure — those belong to later phases (see the
    README's Phase 6 boundary notes). An amount is only ever populated for
    a programme that is actually "eligible" and whose formula this app can
    compute without inventing missing data.
    """

    status: IncentiveEvaluationStatus
    reason: str | None = None

    assessment_id: uuid.UUID | None = None
    technology: RenewableTechnology | None = None
    proposed_capacity_kw: str | None = None
    location: IncentiveLocationSummary | None = None
    consumer_category: TariffConsumerCategory | None = None

    programmes: list[IncentiveEligibilityResult] = Field(default_factory=list)
    summary: IncentiveEvaluationSummary

    calculation_version: str
    calculated_at: datetime


class IncentiveEvaluateRequest(BaseModel):
    assessment_id: uuid.UUID
    # Defaults to today (server-side) when omitted.
    calculation_date: date | None = None
    technology: RenewableTechnology
    proposed_capacity_kw: Decimal = Field(gt=0)


class IncentiveProgramOut(BaseModel):
    """A raw programme row, for GET /api/v1/incentives browsing/debugging."""

    id: uuid.UUID
    scheme_name: str
    scheme_version: str
    description: str | None
    level: IncentiveLevel
    incentive_type: IncentiveType
    state: str | None
    union_territory: str | None
    discom_id: uuid.UUID | None
    consumer_category: TariffConsumerCategory | None
    technology: RenewableTechnology
    min_system_size_kw: Decimal | None
    max_system_size_kw: Decimal | None
    subsidy_type: SubsidyType
    subsidy_value: Decimal | None
    percentage_value: Decimal | None
    maximum_amount: Decimal | None
    verification_status: IncentiveVerificationStatus
    effective_from: date
    effective_to: date | None
    source_name: str | None
    source_url: str | None
    source_document: str | None
    last_verified: date | None
    active: bool

    model_config = {"from_attributes": True}
