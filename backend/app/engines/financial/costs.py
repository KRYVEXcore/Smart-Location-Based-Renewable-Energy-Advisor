"""Verified installed-cost data (backend/app/data/costs/). A cost is only ever read from a record
that names its source, so a system with no matching record has no cost - never a guessed one."""

import json
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

from app.schemas.financial import CostBasis, CostBenchmarkRecord
from app.schemas.recommendation import InrRange

COSTS_ROOT = Path(__file__).resolve().parents[2] / "data" / "costs" / "india"


@lru_cache(maxsize=1)
def load_cost_records() -> tuple[CostBenchmarkRecord, ...]:
    """Every verified record; an invalid file raises here (and in the tests), never silently."""
    records = (
        CostBenchmarkRecord.model_validate(raw)
        for path in sorted(COSTS_ROOT.glob("*.json"))
        for raw in json.loads(path.read_text(encoding="utf-8"))["records"]
    )
    return tuple(record for record in records if record.verification_status == "verified")


def gross_cost(
    records: Sequence[CostBenchmarkRecord], capacity_kw: float, state: str | None, consumer_category: str | None
) -> tuple[InrRange, CostBasis] | None:
    """The gross installed cost of exactly `capacity_kw`, from the record covering this state and
    consumer category; None when there is none. A benchmark is a single figure, so low == high."""
    if state is None or consumer_category is None:
        return None
    for record in records:
        listed = state in record.geographic_scope.states
        in_scope = listed if record.geographic_scope.kind == "only" else not listed
        if in_scope and consumer_category in record.consumer_categories:
            cost = 0.0
            for tier in record.tiers:
                if tier.up_to_kw is not None:
                    cost += min(capacity_kw, tier.up_to_kw) * tier.inr_per_kw
                else:
                    cost += max(capacity_kw - (tier.above_kw or 0), 0) * tier.inr_per_kw
            return InrRange(low=round(cost, 2), high=round(cost, 2)), _basis(record)
    return None


def _basis(record: CostBenchmarkRecord) -> CostBasis:
    scope = record.geographic_scope
    return CostBasis(
        record_id=record.id,
        cost_kind=record.cost_kind,
        name=record.name,
        source_name=record.source_name,
        source_document=record.source_document,
        source_url=record.source_url,
        source_page=record.source_page,
        source_section=record.source_section,
        effective_from=record.effective_from,
        capacity_basis=record.capacity_basis,
        geographic_scope=("all States/UTs except: " if scope.kind == "all_except" else "only: ") + ", ".join(scope.states),
        inclusions=record.inclusions,
        exclusions=record.exclusions,
        gst_treatment=record.gst_treatment,
        verification_status=record.verification_status,
        last_verified=record.last_verified,
    )
