"""Builds the compact, authoritative context SHREA AI is allowed to see.

Everything comes from the assessment row and the existing engine responses
(Phases 4-7); nothing is computed or defaulted here. A section that could not
be produced carries its own status and reason instead of being omitted, so
the model can say "no verified data" rather than guess. Deliberately excluded:
credentials, database details, the street address, and coordinates.
"""

from typing import Any

from app.engines.tariff.consumer_category_mapping import map_building_type_to_consumer_category
from app.models.assessment import Assessment
from app.schemas.incentive import IncentiveEvaluationResponse
from app.schemas.solar import SolarCalculationResponse
from app.schemas.tariff import TariffCalculationResponse
from app.schemas.wind import WindCalculationResponse

# Phase 6 is evaluated for one technology + capacity per request; the dashboard
# uses this same default (see DashboardPage.tsx). It is not a recommendation.
INCENTIVE_TECHNOLOGY = "solar"
INCENTIVE_CAPACITY_KW = 3

NOT_AVAILABLE = {"status": "unavailable", "reason": "This result could not be produced right now."}

APPLICATION_LIMITS = {
    "recommendation_engine": "not implemented - the application gives no recommendation yet",
    "cost_savings_payback_roi": "not implemented - no verified result exists",
    "live_monitoring": "not connected - no live generation, battery or device data exists",
}


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if v is not None and v != [] and v != {}}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _source(source: Any) -> dict | None:
    if source is None:
        return None
    return {
        "name": source.source_name,
        "order": source.source_order_number,
        "page": source.source_page,
        "verification_status": getattr(source.verification_status, "value", source.verification_status),
    }


def _solar(result: SolarCalculationResponse | None) -> dict:
    if result is None:
        return NOT_AVAILABLE
    return {
        "status": result.status,
        "reason": result.reason,
        "annual_consumption_kwh": result.annual_consumption_kwh,
        "resource": [
            {"provider": s.provider, "period": s.period_represented, "unit": s.unit}
            for s in result.data_sources
            if s.category == "solar_resource"
        ],
        "assumptions": {a.name: f"{a.value} {a.unit}" for a in result.assumptions},
        "options": [
            {
                "capacity_kw": o.capacity_kw,
                "annual_generation_kwh": o.estimated_annual_generation_kwh,
                "roof_area_required_sqft": o.roof_area_required_sqft,
                "coverage_percent_of_consumption": o.generation_coverage_percent,
                "technical_status": o.technical_status,
                "notes": o.technical_notes,
            }
            for o in result.options
        ],
    }


def _wind(result: WindCalculationResponse | None) -> dict:
    if result is None:
        return NOT_AVAILABLE
    resource = result.resource
    return {
        "status": result.status,
        "reason": result.reason,
        "resource": None
        if resource is None
        else {
            "provider": resource.provider,
            "period": resource.period_represented,
            "data_type": resource.data_type,
            "mean_speed_mps": resource.used_annual_mean_speed_mps,
            "reference_height_m": resource.used_reference_height_m,
        },
        "candidates": [
            {
                "capacity_kw": c.capacity_kw,
                "annual_generation_kwh": c.annual_generation_kwh,
                "net_capacity_factor": c.net_capacity_factor,
                "technical_status": c.technical_status,
            }
            for c in result.candidates
        ],
        "site_space_note": result.site_space_note,
        "limitations": result.limitations,
    }


def _tariff(result: TariffCalculationResponse | None) -> dict:
    if result is None:
        return NOT_AVAILABLE
    tariff = result.tariff
    return {
        "status": result.status,
        "reason": result.reason,
        "tariff": None
        if tariff is None
        else {
            "name": tariff.tariff_name,
            "version": tariff.tariff_version,
            "effective_from": tariff.effective_from.isoformat(),
            "effective_to": tariff.effective_to.isoformat() if tariff.effective_to else None,
            "source": _source(tariff),
        },
        "monthly_consumption_kwh": result.monthly_consumption_kwh,
        "charges": [
            {"component": c.component, "status": c.status, "amount_inr": c.amount_inr, "notes": c.notes}
            for c in result.charges
        ],
        "estimated_monthly_bill_inr": result.estimated_monthly_bill_inr,
        "is_partial_estimate": result.is_partial_estimate,
        "excluded_components": result.excluded_components,
    }


def _incentives(result: IncentiveEvaluationResponse | None) -> dict:
    if result is None:
        return NOT_AVAILABLE
    return {
        "evaluated_for": {
            "technology": INCENTIVE_TECHNOLOGY,
            "capacity_kw": INCENTIVE_CAPACITY_KW,
            "note": "the dashboard's default evaluation size, not a recommendation",
        },
        "status": result.status,
        "reason": result.reason,
        "calculation_status": result.summary.calculation_status,
        "verified_programmes": result.summary.verified_programmes,
        "programmes": [
            {
                "scheme": p.scheme_name,
                "level": p.level,
                "status": p.status,
                "eligible": p.eligible,
                "reason": p.reason,
                "incentive_amount_inr": p.incentive_amount_inr,
                "calculation_notes": p.calculation_notes,
                "effective_from": p.effective_from.isoformat() if p.effective_from else None,
                "effective_to": p.effective_to.isoformat() if p.effective_to else None,
                "source": _source(p.source),
            }
            for p in result.programmes
        ],
    }


def _has_data(name: str, section: dict) -> bool:
    if name == "incentives":
        return section.get("status") == "ok" and bool(section.get("programmes"))
    return section.get("status") == "ok"


def build_advisor_context(
    assessment: Assessment,
    *,
    solar: SolarCalculationResponse | None,
    wind: WindCalculationResponse | None,
    tariff: TariffCalculationResponse | None,
    incentives: IncentiveEvaluationResponse | None,
) -> dict:
    location = assessment.location
    constraints = assessment.constraints
    building_type = assessment.building.building_type
    tariff_location = tariff.location if tariff else None

    return _clean(
        {
            "location": {
                "city": location.city,
                "district": tariff_location.district if tariff_location else None,
                "state": location.state,
                "country": location.country,
                "discom": tariff_location.discom_name if tariff_location else None,
                "discom_status": tariff_location.discom_status if tariff_location else None,
            },
            "assessment": {
                "building_type": getattr(building_type, "value", building_type),
                "consumer_category": map_building_type_to_consumer_category(building_type).value,
                "monthly_consumption_kwh": _num(assessment.energy.monthly_consumption_kwh),
                "roof_area_sqft": _num(constraints.roof_area_sqft),
                "land_area_sqft": _num(constraints.land_area_sqft),
                "budget_inr": _num(constraints.budget_inr),
                "backup_power_required": constraints.backup_required,
            },
            "solar": _solar(solar),
            "wind": _wind(wind),
            "tariff": _tariff(tariff),
            "incentives": _incentives(incentives),
            "application_limits": APPLICATION_LIMITS,
        }
    )


def _num(value: object | None) -> float | None:
    return None if value is None else float(value)


def available_topics(context: dict) -> dict[str, bool]:
    """Which result sections actually hold verified data (drives suggested questions)."""
    return {name: _has_data(name, context.get(name, {})) for name in ("solar", "wind", "tariff", "incentives")}


def suggested_questions(topics: dict[str, bool]) -> list[str]:
    questions = ["Explain my assessment", "How much electricity am I using?"]
    if topics["solar"]:
        questions.append("Explain my solar result")
    if topics["wind"]:
        questions.append("Explain my wind result")
    if topics["tariff"]:
        questions.append("Explain my tariff")
    if topics["incentives"]:
        questions.append("What incentives are available?")
    return questions
