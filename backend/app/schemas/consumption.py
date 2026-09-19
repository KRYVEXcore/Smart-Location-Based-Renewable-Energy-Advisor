from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

# estimated: a kWh figure (and, when the bill falls in a fixed-charge gap, a range) was derived.
# insufficient_data: no verified applicable tariff could be established, or it cannot explain the bill.
EstimateStatus = Literal["estimated", "insufficient_data"]
EstimateMatch = Literal["within_tolerance", "fixed_charge_gap"]


class BillConsumptionEstimate(BaseModel):
    """An ESTIMATE of monthly consumption derived from the customer's bill. It is never a meter
    reading, and it is derived only by evaluating the existing Tariff Engine - never by dividing
    the bill by a per-unit rate.
    """

    status: EstimateStatus
    reason: str | None = None
    monthly_bill_inr: float
    estimated_monthly_consumption_kwh: float | None = None
    range_low_kwh: float | None = None
    range_high_kwh: float | None = None
    match: EstimateMatch | None = None
    method: str
    source: Literal["user_bill_estimate"] = "user_bill_estimate"

    tariff_name: str | None = None
    tariff_version: str | None = None
    tariff_effective_from: date | None = None
    discom_name: str | None = None
    excluded_components: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    estimated_at: datetime
