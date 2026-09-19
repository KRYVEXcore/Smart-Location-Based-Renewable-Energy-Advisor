import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

# recommended: a technology and size were selected.
# no_suitable_option: the data is complete but no evaluated option is technically feasible.
# insufficient_data: a required input is missing (for example roof area), so nothing is guessed.
RecommendationStatus = Literal["recommended", "no_suitable_option", "insufficient_data"]

# Why a solar candidate was or was not chosen.
SolarDecision = Literal[
    "selected",
    "selected_best_available",
    "larger_than_needed",
    "below_target",
    "excluded_infeasible",
    "excluded_insufficient_data",
]


class EvaluatedSolarOption(BaseModel):
    capacity_kw: float
    annual_generation_kwh: float | None = None
    coverage_percent: float | None = None
    technical_status: str
    decision: SolarDecision
    note: str | None = None


class ExcludedOption(BaseModel):
    technology: Literal["solar", "wind", "hybrid", "battery"]
    reason_code: str
    reason: str


class RecommendedIncentive(BaseModel):
    scheme_name: str
    level: str
    incentive_amount_inr: str | None = None
    calculation_notes: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    source_name: str | None = None
    source_order: str | None = None
    source_page: str | None = None
    verification_status: str | None = None


class IncentiveContext(BaseModel):
    """What the (existing) Incentive Engine said for the recommended system, unchanged."""

    evaluated_technology: str | None = None
    evaluated_capacity_kw: str | None = None
    status: str
    eligible_programmes: int = 0
    note: str


class TariffContext(BaseModel):
    status: str
    reason: str | None = None
    tariff_name: str | None = None
    tariff_version: str | None = None
    effective_from: date | None = None
    estimated_monthly_bill_inr: str | None = None
    is_partial_estimate: bool | None = None


class CostContext(BaseModel):
    """There is no verified cost data, so cost, savings and payback are never produced."""

    status: Literal["not_available"] = "not_available"
    budget_inr: float | None = None
    note: str


class RecommendationResult(BaseModel):
    recommendation_status: RecommendationStatus
    assessment_id: uuid.UUID | None = None

    recommended_technology: Literal["solar", "wind"] | None = None
    recommended_capacity_kw: float | None = None
    technical_feasibility: Literal["technically_feasible"] | None = None
    annual_consumption_kwh: float | None = None
    expected_annual_generation_kwh: float | None = None
    coverage_percent: float | None = None
    target_coverage_percent: float
    target_met: bool | None = None

    reason_code: str
    recommendation_reason: str

    solar_options_evaluated: list[EvaluatedSolarOption] = Field(default_factory=list)
    excluded_options: list[ExcludedOption] = Field(default_factory=list)
    applicable_incentives: list[RecommendedIncentive] = Field(default_factory=list)
    incentive_context: IncentiveContext | None = None
    tariff_context: TariffContext | None = None
    cost_context: CostContext
    limitations: list[str] = Field(default_factory=list)

    rules: list[str] = Field(default_factory=list)
    recommendation_version: str
    engine_versions: dict[str, str] = Field(default_factory=dict)
    calculated_at: datetime
