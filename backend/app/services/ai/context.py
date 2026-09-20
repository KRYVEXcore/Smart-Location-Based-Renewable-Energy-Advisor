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
from app.schemas.financial import FinancialAnalysisResult
from app.schemas.incentive import IncentiveEvaluationResponse
from app.schemas.recommendation import RecommendationResult
from app.schemas.solar import SolarCalculationResponse
from app.schemas.tariff import TariffCalculationResponse
from app.schemas.wind import WindCalculationResponse

NOT_AVAILABLE = {"status": "unavailable", "reason": "This result could not be produced right now."}

APPLICATION_LIMITS = {
    "financial_analysis": "deterministic estimates only (see the financial_analysis section); any value it lacks is unavailable",
    "roi_and_future_returns": "not calculated",
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


def _recommendation(result: RecommendationResult | None) -> dict:
    if result is None:
        return NOT_AVAILABLE
    return {
        "status": result.recommendation_status,
        "recommended_technology": result.recommended_technology,
        "recommended_capacity_kw": result.recommended_capacity_kw,
        "technical_feasibility": result.technical_feasibility,
        "annual_consumption_kwh": result.annual_consumption_kwh,
        "expected_annual_generation_kwh": result.expected_annual_generation_kwh,
        "coverage_percent": result.coverage_percent,
        "target_coverage_percent": result.target_coverage_percent,
        "target_met": result.target_met,
        "reason": result.recommendation_reason,
        "solar_options_evaluated": [
            {"capacity_kw": o.capacity_kw, "coverage_percent": o.coverage_percent, "decision": o.decision, "note": o.note}
            for o in result.solar_options_evaluated
        ],
        "excluded_options": [{"technology": e.technology, "reason": e.reason} for e in result.excluded_options],
        "applicable_incentives": [
            {
                "scheme": i.scheme_name,
                "level": i.level,
                "incentive_amount_inr": i.incentive_amount_inr,
                "effective_from": i.effective_from.isoformat() if i.effective_from else None,
                "effective_to": i.effective_to.isoformat() if i.effective_to else None,
                "source_name": i.source_name,
                "source_order": i.source_order,
                "source_page": i.source_page,
            }
            for i in result.applicable_incentives
        ],
        "incentive_note": result.incentive_context.note if result.incentive_context else None,
        "cost": result.cost_context.note,
        "budget_inr": result.cost_context.budget_inr,
        "limitations": result.limitations,
    }


def _financial(result: FinancialAnalysisResult | None) -> dict:
    """The Financial Analysis Engine's result, unchanged. The model may quote these figures and must
    not recompute them; a value the engine could not support is simply absent (see status/reason)."""
    if result is None:
        return NOT_AVAILABLE
    basis = result.cost_basis
    return {
        "status": result.status,
        "reason": result.reason,
        "technology": result.technology,
        "capacity_kw": result.capacity_kw,
        "gross_cost_range_inr": result.gross_cost_range_inr.model_dump() if result.gross_cost_range_inr else None,
        "cost_basis": None
        if basis is None
        else {
            "kind": basis.cost_kind,
            "source": basis.source_name,
            "document": basis.source_document,
            "effective_from": basis.effective_from.isoformat(),
            "capacity_basis": basis.capacity_basis,
            "gst_treatment": basis.gst_treatment,
            "inclusions": basis.inclusions,
            "exclusions": basis.exclusions,
        },
        "incentive_inr": result.incentive_inr,
        "incentive_scheme": result.incentive_scheme,
        "incentive_note": result.incentive_note,
        "net_investment_range_inr": result.net_investment_range_inr.model_dump() if result.net_investment_range_inr else None,
        "estimated_annual_savings_inr": result.annual_savings_inr,
        "estimated_monthly_savings_inr": result.monthly_savings_inr,
        "baseline_annual_bill_inr": result.baseline_annual_bill_inr,
        "annual_bill_after_solar_inr": result.annual_bill_after_solar_inr,
        "annual_surplus_generation_kwh_not_valued": result.annual_surplus_generation_kwh,
        "estimated_simple_payback_years_range": result.simple_payback_years_range.model_dump()
        if result.simple_payback_years_range
        else None,
        "payback_note": result.payback_note,
        "tariff": result.tariff_name,
        "methodology": result.methodology,
        "limitations": result.limitations,
    }


def _incentives(result: IncentiveEvaluationResponse | None, recommendation: RecommendationResult | None) -> dict:
    if result is None:
        return NOT_AVAILABLE
    recommended = recommendation is not None and recommendation.recommendation_status == "recommended"
    return {
        "evaluated_for": {
            "technology": result.technology.value if result.technology else None,
            "capacity_kw": result.proposed_capacity_kw,
            "note": "the recommended system"
            if recommended
            else "the dashboard's default evaluation size, not a recommendation",
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


def _consumption(assessment: Assessment) -> dict:
    """The customer's bill comes first; kWh is either theirs or an estimate derived from the bill."""
    energy = assessment.energy
    estimated = energy.consumption_source == "user_bill_estimate"
    estimate = energy.consumption_estimate or {}
    return {
        "monthly_electricity_bill_inr": _num(energy.monthly_electricity_bill_inr),
        "monthly_consumption_kwh": _num(energy.monthly_consumption_kwh),
        "consumption_source": energy.consumption_source,
        "consumption_basis": (
            "an ESTIMATE derived from the monthly bill with the verified tariff - not a meter reading"
            if estimated
            else "entered by the customer as units (kWh)"
        ),
        "consumption_estimate": None
        if not estimated
        else {
            "status": estimate.get("status"),
            "reason": estimate.get("reason"),
            "range_low_kwh": estimate.get("range_low_kwh"),
            "range_high_kwh": estimate.get("range_high_kwh"),
            "tariff": estimate.get("tariff_name"),
            "tariff_version": estimate.get("tariff_version"),
            "limitations": estimate.get("limitations"),
        },
    }


def _has_data(name: str, section: dict) -> bool:
    if name == "incentives":
        return section.get("status") == "ok" and bool(section.get("programmes"))
    if name == "recommendation":
        return section.get("status") == "recommended"
    if name == "financial_analysis":
        return section.get("status") in ("complete", "cost_unavailable", "savings_unavailable")
    return section.get("status") == "ok"


def build_advisor_context(
    assessment: Assessment,
    *,
    solar: SolarCalculationResponse | None,
    wind: WindCalculationResponse | None,
    tariff: TariffCalculationResponse | None,
    incentives: IncentiveEvaluationResponse | None,
    recommendation: RecommendationResult | None,
    financial: FinancialAnalysisResult | None = None,
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
                **_consumption(assessment),
                "roof_area_sqft": _num(constraints.roof_area_sqft),
                "land_area_sqft": _num(constraints.land_area_sqft),
                "budget_inr": _num(constraints.budget_inr),
                "backup_power_required": constraints.backup_required,
            },
            "solar": _solar(solar),
            "wind": _wind(wind),
            "tariff": _tariff(tariff),
            "incentives": _incentives(incentives, recommendation),
            "recommendation": _recommendation(recommendation),
            "financial_analysis": _financial(financial),
            "application_limits": APPLICATION_LIMITS,
        }
    )


def _num(value: object | None) -> float | None:
    return None if value is None else float(value)


def available_topics(context: dict) -> dict[str, bool]:
    """Which result sections actually hold verified data (drives suggested questions)."""
    return {name: _has_data(name, context.get(name, {})) for name in ("solar", "wind", "tariff", "incentives", "recommendation", "financial_analysis")}


def suggested_questions(topics: dict[str, bool]) -> list[str]:
    questions = ["Explain my assessment", "How much electricity am I using?"]
    if topics["recommendation"]:
        questions.insert(0, "What do you recommend for me?")
    if topics["solar"]:
        questions.append("Explain my solar result")
    if topics["wind"]:
        questions.append("Explain my wind result")
    if topics["tariff"]:
        questions.append("Explain my tariff")
    if topics["incentives"]:
        questions.append("What incentives are available?")
    if topics["financial_analysis"]:
        questions.extend(["What will my system cost?", "What will I save?", "What is my payback?"])
    return questions
