"""Typed, validated shapes for the JSON files in backend/app/data/.

`load_json` parses numbers as Decimal (never float) so a rate such as 4.95
is stored exactly. A record whose `verification_status` is "verified" must
carry a complete, official source: organisation, official HTTPS URL,
document, order/notification number, page, table-or-section, the quoted
excerpt, and the date it was last verified. Anything less must be
`pending_review` / `unavailable` and inactive: never a "verified" number
without a locator.
"""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.india_geography import INDIAN_STATES, INDIAN_UNION_TERRITORIES
from app.data_validation.official_sources import is_official_source_url
from app.models.enums import (
    FixedChargeBasis,
    IncentiveLevel,
    IncentiveType,
    IncentiveVerificationStatus,
    RenewableTechnology,
    SubsidyType,
    TariffConsumerCategory,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    url: str | None = None
    document: str | None = None
    order_number: str | None = None
    order_date: date | None = None
    page: str | None = None
    table: str | None = None
    section: str | None = None
    excerpt: str | None = None
    last_verified: date | None = None

    def problems_for_verified(self) -> list[str]:
        problems: list[str] = []
        for field in ("name", "url", "document", "order_number", "page", "excerpt", "last_verified"):
            value = getattr(self, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                problems.append(f"source.{field} is required for a verified record")
        if not (self.table or self.section):
            problems.append("source.table or source.section is required for a verified record")
        if self.url and not is_official_source_url(self.url):
            problems.append(f"source.url is not an official Indian source: {self.url}")
        return problems


def _check_jurisdiction(state: str | None, union_territory: str | None) -> None:
    if (state is None) == (union_territory is None):
        raise ValueError("Exactly one of state / union_territory must be set.")
    if state is not None and state not in INDIAN_STATES:
        raise ValueError(f"Unknown state: {state!r}")
    if union_territory is not None and union_territory not in INDIAN_UNION_TERRITORIES:
        raise ValueError(f"Unknown union territory: {union_territory!r}")


def _check_verified_source(status: IncentiveVerificationStatus, source: SourceRecord) -> None:
    if status == IncentiveVerificationStatus.VERIFIED:
        problems = source.problems_for_verified()
        if problems:
            raise ValueError("; ".join(problems))


class TariffSlabRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slab_min_kwh: Decimal
    slab_max_kwh: Decimal | None = None
    energy_charge_inr_per_kwh: Decimal
    fixed_charge_inr: Decimal | None = None
    wheeling_charge_inr_per_kwh: Decimal | None = None

    @field_validator(
        "slab_min_kwh",
        "slab_max_kwh",
        "energy_charge_inr_per_kwh",
        "fixed_charge_inr",
        "wheeling_charge_inr_per_kwh",
        mode="before",
    )
    @classmethod
    def _no_floats(cls, value: Any) -> Any:
        if isinstance(value, float):
            raise ValueError("Numbers must be parsed as Decimal, never float (use records.load_json).")
        return value


class TariffScheduleRecord(BaseModel):
    """One tariff schedule: every slab row that shares a tariff_version."""

    model_config = ConfigDict(extra="forbid")

    state: str | None = None
    union_territory: str | None = None
    discom_short_code: str | None = None
    consumer_category: TariffConsumerCategory
    tariff_version: str
    tariff_name: str
    effective_from: date
    effective_to: date | None = None
    fixed_charge_basis: FixedChargeBasis | None = None
    verification_status: IncentiveVerificationStatus
    active: bool = True
    source: SourceRecord
    verification_notes: str | None = None
    slabs: list[TariffSlabRecord]

    @model_validator(mode="after")
    def _validate(self) -> "TariffScheduleRecord":
        _check_jurisdiction(self.state, self.union_territory)
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to is before effective_from.")
        if any(slab.fixed_charge_inr is not None for slab in self.slabs) and self.fixed_charge_basis is None:
            raise ValueError("fixed_charge_basis is required when any slab has a fixed_charge_inr.")
        if self.active and self.verification_status != IncentiveVerificationStatus.VERIFIED:
            raise ValueError("An unverified record must not be active.")
        if not self.slabs:
            raise ValueError("At least one slab is required.")
        _check_verified_source(self.verification_status, self.source)
        return self

    def natural_key(self) -> tuple[str, str | None, str, str]:
        return (
            self.state or self.union_territory or "",
            self.discom_short_code,
            self.consumer_category.value,
            self.tariff_version,
        )


class IncentiveRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_name: str
    scheme_version: str
    description: str | None = None
    level: IncentiveLevel
    incentive_type: IncentiveType
    state: str | None = None
    union_territory: str | None = None
    discom_short_code: str | None = None
    consumer_category: TariffConsumerCategory | None = None
    technology: RenewableTechnology
    min_system_size_kw: Decimal | None = None
    max_system_size_kw: Decimal | None = None
    subsidy_type: SubsidyType
    subsidy_value: Decimal | None = None
    percentage_value: Decimal | None = None
    maximum_amount: Decimal | None = None
    calculation_rules: dict | None = None
    eligibility_rules: dict | None = None
    application_requirements: dict | None = None
    stacking_rules: dict | None = None
    effective_from: date
    effective_to: date | None = None
    verification_status: IncentiveVerificationStatus
    active: bool = True
    source: SourceRecord
    verification_notes: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> "IncentiveRecord":
        if self.state is not None or self.union_territory is not None:
            _check_jurisdiction(self.state, self.union_territory)
        if self.level == IncentiveLevel.STATE and self.state is None and self.union_territory is None:
            raise ValueError("A state-level scheme needs a state or union_territory.")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to is before effective_from.")
        if self.active and self.verification_status != IncentiveVerificationStatus.VERIFIED:
            raise ValueError("An unverified record must not be active.")
        _check_verified_source(self.verification_status, self.source)
        return self

    def natural_key(self) -> tuple[str, str, str, str]:
        return (self.scheme_name, self.level.value, self.technology.value, self.scheme_version)


class DiscomRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    short_code: str
    state: str | None = None
    union_territory: str | None = None
    is_active: bool = True
    source: SourceRecord

    @model_validator(mode="after")
    def _validate(self) -> "DiscomRecord":
        _check_jurisdiction(self.state, self.union_territory)
        if not self.source.url or not is_official_source_url(self.source.url):
            raise ValueError("A DISCOM must cite an official source URL.")
        if not (self.source.document and self.source.last_verified):
            raise ValueError("A DISCOM must cite the source document and the date it was verified.")
        return self
