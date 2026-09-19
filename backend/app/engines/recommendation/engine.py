"""Recommendation Engine: chooses a technology and size from the OUTPUTS of the existing
engines. It never recalculates generation, resource, tariff or incentive values, never
calls a provider or the database, and involves no AI. Given the same inputs it always
returns the same recommendation (only `calculated_at` differs).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.engines.recommendation.assumptions import (
    BUDGET_UNAVAILABLE_NOTE,
    COST_UNAVAILABLE_NOTE,
    RECOMMENDATION_VERSION,
    RULES,
    TARGET_ANNUAL_COVERAGE_PERCENT,
)
from app.schemas.incentive import IncentiveEvaluationResponse
from app.schemas.recommendation import (
    CostContext,
    EvaluatedSolarOption,
    ExcludedOption,
    IncentiveContext,
    RecommendationResult,
    RecommendedIncentive,
    TariffContext,
)
from app.schemas.solar import SolarCalculationResponse, SolarSystemOption
from app.schemas.tariff import TariffCalculationResponse
from app.schemas.wind import WindCalculationResponse, WindCandidate

# (technology, capacity_kw) -> the existing Incentive Engine's answer for exactly that system.
IncentivesFor = Callable[[str, float], IncentiveEvaluationResponse | None]


@dataclass(frozen=True)
class RecommendationInput:
    monthly_consumption_kwh: float
    roof_area_sqft: float | None
    budget_inr: float | None
    backup_required: bool
    solar: SolarCalculationResponse | None
    wind: WindCalculationResponse | None
    tariff: TariffCalculationResponse | None


def recommend(engine_input: RecommendationInput, incentives_for: IncentivesFor) -> RecommendationResult:
    target = TARGET_ANNUAL_COVERAGE_PERCENT
    solar_options, solar_pick, solar_met = _select_solar(engine_input.solar, target)
    wind_pick, wind_met = _select_wind(engine_input.wind, _annual_consumption(engine_input), target)

    if solar_pick is not None:
        technology, capacity = "solar", solar_pick.capacity_kw
        generation, coverage, met = solar_pick.estimated_annual_generation_kwh, solar_pick.generation_coverage_percent, solar_met
    elif wind_pick is not None:
        technology, capacity = "wind", wind_pick.capacity_kw
        generation, coverage, met = wind_pick.annual_generation_kwh, _coverage(wind_pick.annual_generation_kwh, _annual_consumption(engine_input)), wind_met
    else:
        technology = capacity = generation = coverage = met = None

    status, reason_code, reason = _describe(engine_input, technology, capacity, coverage, met, solar_options, target)
    incentives = incentives_for(technology, capacity) if technology and capacity else None

    return RecommendationResult(
        recommendation_status=status,
        recommended_technology=technology,
        recommended_capacity_kw=capacity,
        technical_feasibility="technically_feasible" if technology else None,
        annual_consumption_kwh=_annual_consumption(engine_input),
        expected_annual_generation_kwh=generation,
        coverage_percent=coverage,
        target_coverage_percent=target,
        target_met=met,
        reason_code=reason_code,
        recommendation_reason=reason,
        solar_options_evaluated=solar_options,
        excluded_options=_excluded(engine_input, technology, wind_pick),
        applicable_incentives=_applicable(incentives, technology),
        incentive_context=_incentive_context(incentives, technology),
        tariff_context=_tariff_context(engine_input.tariff),
        cost_context=CostContext(
            budget_inr=engine_input.budget_inr,
            note=BUDGET_UNAVAILABLE_NOTE if engine_input.budget_inr else COST_UNAVAILABLE_NOTE,
        ),
        limitations=_limitations(engine_input, technology, incentives, solar_options, met),
        rules=RULES,
        recommendation_version=RECOMMENDATION_VERSION,
        engine_versions=_versions(engine_input),
        calculated_at=datetime.now(UTC),
    )


def _annual_consumption(engine_input: RecommendationInput) -> float:
    solar = engine_input.solar
    if solar is not None and solar.annual_consumption_kwh is not None:
        return solar.annual_consumption_kwh
    return round(engine_input.monthly_consumption_kwh * 12, 1)


def _coverage(generation_kwh: float, annual_consumption_kwh: float) -> float | None:
    # Same definition the Solar Engine uses for its own coverage figure.
    return round(generation_kwh / annual_consumption_kwh * 100, 1) if annual_consumption_kwh > 0 else None


def _select_solar(
    solar: SolarCalculationResponse | None, target: float
) -> tuple[list[EvaluatedSolarOption], SolarSystemOption | None, bool | None]:
    if solar is None or solar.status != "ok":
        return [], None, None

    options = sorted(solar.options, key=lambda option: option.capacity_kw)
    feasible = [
        o
        for o in options
        if o.technical_status == "technically_feasible"
        and o.estimated_annual_generation_kwh is not None
        and o.generation_coverage_percent is not None
    ]
    meeting = [o for o in feasible if (o.generation_coverage_percent or 0) >= target]
    pick = meeting[0] if meeting else (feasible[-1] if feasible else None)  # options are sorted by size

    evaluated = [_solar_decision(o, pick, bool(meeting), target) for o in options]
    return evaluated, pick, (bool(meeting) if pick is not None else None)


def _solar_decision(
    option: SolarSystemOption, pick: SolarSystemOption | None, target_met: bool, target: float
) -> EvaluatedSolarOption:
    note: str | None = "; ".join(option.technical_notes) or None
    if option.technical_status == "technically_infeasible":
        decision = "excluded_infeasible"
    elif option.technical_status != "technically_feasible":
        decision = "excluded_insufficient_data"
    elif pick is not None and option.capacity_kw == pick.capacity_kw:
        decision = "selected" if target_met else "selected_best_available"
    elif (option.generation_coverage_percent or 0) >= target:
        decision = "larger_than_needed"
    else:
        decision = "below_target"
    return EvaluatedSolarOption(
        capacity_kw=option.capacity_kw,
        annual_generation_kwh=option.estimated_annual_generation_kwh,
        coverage_percent=option.generation_coverage_percent,
        technical_status=option.technical_status,
        decision=decision,
        note=note,
    )


def _select_wind(
    wind: WindCalculationResponse | None, annual_consumption_kwh: float, target: float
) -> tuple[WindCandidate | None, bool | None]:
    if wind is None or wind.status != "ok":
        return None, None
    feasible = sorted(
        (c for c in wind.candidates if c.technical_status == "technically_feasible"), key=lambda c: c.capacity_kw
    )
    if not feasible:
        return None, None
    meeting = [c for c in feasible if (_coverage(c.annual_generation_kwh, annual_consumption_kwh) or 0) >= target]
    return (meeting[0], True) if meeting else (feasible[-1], False)


def _describe(
    engine_input: RecommendationInput,
    technology: str | None,
    capacity: float | None,
    coverage: float | None,
    target_met: bool | None,
    solar_options: list[EvaluatedSolarOption],
    target: float,
) -> tuple[str, str, str]:
    if technology is not None and capacity is not None:
        if target_met:
            return (
                "recommended",
                "smallest_capacity_meeting_target",
                f"Smallest evaluated {technology} capacity that is technically feasible and reaches the "
                f"{target:g}% annual coverage target.",
            )
        return (
            "recommended",
            "highest_feasible_below_target",
            f"No technically feasible {technology} capacity reaches the {target:g}% annual coverage target. "
            f"{capacity:g} kW is the largest technically feasible evaluated size and covers {coverage}% of annual consumption.",
        )

    solar = engine_input.solar
    if solar is None or solar.status != "ok":
        return (
            "insufficient_data",
            "solar_result_unavailable",
            "No recommendation can be made because the solar result is unavailable"
            + (f": {solar.reason}" if solar and solar.reason else "."),
        )
    if any(o.decision == "excluded_insufficient_data" for o in solar_options):
        return (
            "insufficient_data",
            "site_data_missing",
            "No recommendation can be made because a required input is missing, such as the roof area, "
            "so technical feasibility cannot be checked.",
        )
    return (
        "no_suitable_option",
        "no_feasible_option",
        "No evaluated option is technically feasible for this site, so no system is recommended.",
    )


def _excluded(
    engine_input: RecommendationInput, technology: str | None, wind_pick: WindCandidate | None
) -> list[ExcludedOption]:
    excluded: list[ExcludedOption] = []
    if technology != "solar":
        excluded.append(
            ExcludedOption(
                technology="solar",
                reason_code="no_feasible_solar",
                reason="No technically feasible solar capacity was found for this assessment.",
            )
        )
    if technology != "wind":
        excluded.append(_wind_exclusion(engine_input.wind, wind_pick))
    excluded.append(
        ExcludedOption(
            technology="hybrid",
            reason_code="hybrid_not_evaluated",
            reason="Hybrid (solar + wind) is not recommended: there is no deterministic hybrid engine yet.",
        )
    )
    excluded.append(
        ExcludedOption(
            technology="battery",
            reason_code="battery_not_sized",
            reason="Battery storage is not sized: there is no deterministic battery calculation yet.",
        )
    )
    return excluded


def _wind_exclusion(wind: WindCalculationResponse | None, wind_pick: WindCandidate | None) -> ExcludedOption:
    if wind_pick is not None:
        return ExcludedOption(
            technology="wind",
            reason_code="solar_preferred",
            reason="Wind is technically feasible but not selected: solar is preferred when both are feasible, "
            "because the wind screening is a regional estimate rather than a site measurement.",
        )
    if wind is None or wind.status != "ok":
        detail = f" {wind.reason}" if wind and wind.reason else ""
        return ExcludedOption(
            technology="wind",
            reason_code="wind_resource_unavailable",
            reason=f"Wind is not recommended because there is no verified wind result for this location.{detail}",
        )
    statuses = {c.technical_status for c in wind.candidates}
    if "marginal" in statuses:
        return ExcludedOption(
            technology="wind",
            reason_code="wind_marginal",
            reason="Wind is not recommended because the validated wind resource screening is only marginal.",
        )
    return ExcludedOption(
        technology="wind",
        reason_code="insufficient_wind_resource",
        reason="Wind is not recommended because the validated wind resource screening is insufficient.",
    )


def _applicable(incentives: IncentiveEvaluationResponse | None, technology: str | None) -> list[RecommendedIncentive]:
    if incentives is None or technology is None:
        return []
    found = []
    for programme in incentives.programmes:
        if not programme.eligible or programme.technology.value != technology:
            continue
        source = programme.source
        found.append(
            RecommendedIncentive(
                scheme_name=programme.scheme_name,
                level=programme.level.value,
                incentive_amount_inr=programme.incentive_amount_inr,
                calculation_notes=programme.calculation_notes,
                effective_from=programme.effective_from,
                effective_to=programme.effective_to,
                source_name=source.source_name if source else None,
                source_order=source.source_order_number if source else None,
                source_page=source.source_page if source else None,
                verification_status=source.verification_status.value if source and source.verification_status else None,
            )
        )
    return found


def _incentive_context(incentives: IncentiveEvaluationResponse | None, technology: str | None) -> IncentiveContext | None:
    if technology is None:
        return None
    if incentives is None:
        return IncentiveContext(status="unavailable", note="The incentive result could not be produced right now.")
    eligible = sum(1 for p in incentives.programmes if p.eligible and p.technology.value == technology)
    if eligible:
        note = f"{eligible} verified programme(s) apply to this system."
    elif incentives.programmes:
        note = "Verified programmes were evaluated for this case and none applies to it."
    elif incentives.status == "ok":
        note = "No verified incentive is currently configured for this location and system."
    else:
        note = incentives.reason or "Incentive eligibility could not be evaluated."
    return IncentiveContext(
        evaluated_technology=incentives.technology.value if incentives.technology else None,
        evaluated_capacity_kw=incentives.proposed_capacity_kw,
        status=incentives.summary.calculation_status,
        eligible_programmes=eligible,
        note=note,
    )


def _tariff_context(tariff: TariffCalculationResponse | None) -> TariffContext | None:
    if tariff is None:
        return TariffContext(status="unavailable", reason="The tariff result could not be produced right now.")
    schedule = tariff.tariff
    return TariffContext(
        status=tariff.status,
        reason=tariff.reason,
        tariff_name=schedule.tariff_name if schedule else None,
        tariff_version=schedule.tariff_version if schedule else None,
        effective_from=schedule.effective_from if schedule else None,
        estimated_monthly_bill_inr=tariff.estimated_monthly_bill_inr,
        is_partial_estimate=tariff.is_partial_estimate if tariff.status == "ok" else None,
    )


def _limitations(
    engine_input: RecommendationInput,
    technology: str | None,
    incentives: IncentiveEvaluationResponse | None,
    solar_options: list[EvaluatedSolarOption],
    target_met: bool | None,
) -> list[str]:
    limits = [BUDGET_UNAVAILABLE_NOTE if engine_input.budget_inr else COST_UNAVAILABLE_NOTE]
    if technology is not None:
        limits.append("Technical screening only: a site survey, structural check and utility approval are still required.")
    if technology is not None and target_met is False:
        roof_limited = any(o.decision == "excluded_infeasible" for o in solar_options)
        limits.append(
            "The annual coverage target cannot be fully reached"
            + (" with the available roof area." if roof_limited else " with the evaluated capacities.")
        )
    if engine_input.backup_required:
        limits.append("Backup power was requested, but battery sizing is not currently calculated.")
    tariff = engine_input.tariff
    if tariff is None or tariff.status != "ok":
        limits.append("No verified tariff is available for this location, so the electricity bill context is unavailable.")
    if technology is not None and (incentives is None or not any(p.eligible for p in incentives.programmes)):
        limits.append("No verified incentive currently applies to this case.")
    return limits


def _versions(engine_input: RecommendationInput) -> dict[str, str]:
    versions: dict[str, str] = {}
    if engine_input.solar is not None:
        versions["solar"] = engine_input.solar.calculation_version
    if engine_input.wind is not None:
        versions["wind"] = engine_input.wind.calculation_version
    if engine_input.tariff is not None:
        versions["tariff"] = engine_input.tariff.calculation_version
    return versions
