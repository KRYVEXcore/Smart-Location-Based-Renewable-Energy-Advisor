import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.recommendation import InrRange, YearsRange

# complete: verified cost and modelled savings are both available (payback too when savings > 0).
# cost_unavailable: no verified cost data applies; savings may still be modelled.
# savings_unavailable: cost is known but savings cannot be modelled safely.
# insufficient_data: neither cost nor savings can be produced from the available data.
# not_applicable: there is no recommended system to analyse.
FinancialStatus = Literal["complete", "cost_unavailable", "savings_unavailable", "insufficient_data", "not_applicable"]


class CostTier(BaseModel):
    """Either the first `up_to_kw` kW or every kW `above_kw`, at `inr_per_kw`."""

    up_to_kw: float | None = None
    above_kw: float | None = None
    inr_per_kw: float

    @model_validator(mode="after")
    def _one_bound(self) -> "CostTier":
        if (self.up_to_kw is None) == (self.above_kw is None):
            raise ValueError("a tier needs exactly one of up_to_kw / above_kw")
        return self


class GeographicScope(BaseModel):
    kind: Literal["all_except", "only"]
    states: list[str]


class CostBenchmarkRecord(BaseModel):
    """One verified cost source. Every provenance field is required, so a record that cannot say
    where it came from cannot be loaded (and therefore cannot produce a cost)."""

    id: str
    technology: Literal["solar_rooftop"]
    consumer_categories: list[str]
    cost_kind: Literal["benchmark"]
    name: str
    tiers: list[CostTier]
    geographic_scope: GeographicScope
    source_name: str
    source_document: str
    source_url: str
    source_page: str
    source_section: str
    source_excerpt: str
    effective_from: date
    document_date: date | None = None
    capacity_basis: str
    inclusions: str
    exclusions: str
    gst_treatment: str
    verification_status: Literal["verified", "pending_review"]
    last_verified: date
    verification_notes: str | None = None

    @model_validator(mode="after")
    def _has_tiers(self) -> "CostBenchmarkRecord":
        if not self.tiers:
            raise ValueError("a cost record needs at least one tier")
        return self


class CostBasis(BaseModel):
    """Where the gross cost came from, so it can be audited."""

    record_id: str
    cost_kind: str
    name: str
    source_name: str
    source_document: str
    source_url: str
    source_page: str
    source_section: str
    effective_from: date
    capacity_basis: str
    geographic_scope: str
    inclusions: str
    exclusions: str
    gst_treatment: str
    verification_status: str
    last_verified: date


class FinancialAnalysisResult(BaseModel):
    """Deterministic, estimated financial analysis of the RECOMMENDED system. No AI is involved,
    nothing is guaranteed, and a value that cannot be supported is None, never zero."""

    status: FinancialStatus
    reason: str | None = None
    assessment_id: uuid.UUID | None = None

    technology: Literal["solar", "wind"] | None = None
    capacity_kw: float | None = None

    # Cost (verified dataset)
    cost_status: Literal["available", "not_available"] = "not_available"
    gross_cost_range_inr: InrRange | None = None
    cost_basis: CostBasis | None = None
    # Incentive (existing Incentive Engine result for exactly this system)
    incentive_inr: float | None = None
    incentive_scheme: str | None = None
    incentive_note: str | None = None
    net_investment_range_inr: InrRange | None = None

    # Savings (existing Tariff Engine, modelled consumption offset only)
    savings_status: Literal["available", "not_available"] = "not_available"
    annual_savings_inr: float | None = None
    monthly_savings_inr: float | None = None
    baseline_annual_bill_inr: float | None = None
    annual_bill_after_solar_inr: float | None = None
    annual_self_consumed_kwh: float | None = None
    annual_surplus_generation_kwh: float | None = None
    tariff_name: str | None = None
    tariff_version: str | None = None

    simple_payback_years_range: YearsRange | None = None
    payback_note: str | None = None

    methodology: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    calculation_version: str
    calculated_at: datetime
