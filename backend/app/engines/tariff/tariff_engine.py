"""Tariff Engine entry point.

Pure calculation: given a consumption figure and a set of candidate tariff
slab rows already scoped to the right state/DISCOM/consumer-category (see
app.services.tariff_calculation_service — this module never touches the
database, FastAPI, or a location provider), selects the tariff version
applicable on calculation_date and computes an estimated baseline grid
electricity bill.

No solar cost, subsidy, saving, or payback is computed here — see the
README's Phase 5 boundary notes.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from app.engines.tariff.bill_calculation import calculate_charge_components, sum_included_charges
from app.engines.tariff.version import ENGINE_CALCULATION_VERSION
from app.engines.tariff.version_selection import select_applicable_version_rows
from app.models.enums import TariffConsumerCategory
from app.schemas.tariff import TariffCalculationResponse, TariffScheduleSummary, TariffSlabInput


def calculate_bill_for_grid_consumption(
    monthly_consumption_kwh: Decimal,
    candidate_rows: list[TariffSlabInput],
    calculation_date: date,
    consumer_category: TariffConsumerCategory,
) -> TariffCalculationResponse:
    """Reusable by future phases needing a grid-only bill estimate (e.g. a
    future savings engine comparing grid cost against a solar-offset
    scenario) without recomputing tariff resolution themselves.
    """
    now = datetime.now(UTC)

    applicable_rows = select_applicable_version_rows(candidate_rows, calculation_date)
    if not applicable_rows:
        return TariffCalculationResponse(
            status="tariff_not_configured",
            reason=(
                "Tariff data exists for this location and category, but none of it covers "
                f"{calculation_date.isoformat()}."
            ),
            consumer_category=consumer_category,
            calculation_version=ENGINE_CALCULATION_VERSION,
            calculated_at=now,
        )

    charges = calculate_charge_components(monthly_consumption_kwh, applicable_rows)
    estimated_bill = sum_included_charges(charges)
    excluded = [
        f"{component.component}_charge_not_calculated"
        for component in charges
        if component.status == "not_calculated"
    ]

    sample_row = applicable_rows[0]
    schedule = TariffScheduleSummary(
        tariff_name=sample_row.tariff_name,
        tariff_version=sample_row.tariff_version,
        consumer_category=consumer_category,
        effective_from=sample_row.effective_from,
        effective_to=sample_row.effective_to,
        source_url=sample_row.source_url,
        source_document=sample_row.source_document,
        source_name=sample_row.source_name,
        last_verified=sample_row.last_verified,
    )

    return TariffCalculationResponse(
        status="ok",
        consumer_category=consumer_category,
        tariff=schedule,
        monthly_consumption_kwh=str(monthly_consumption_kwh),
        charges=charges,
        estimated_monthly_bill_inr=str(estimated_bill),
        is_partial_estimate=bool(excluded),
        excluded_components=excluded,
        calculation_version=ENGINE_CALCULATION_VERSION,
        calculated_at=now,
    )
