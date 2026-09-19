import type { RecommendationResult, SolarDecision } from '../types/recommendation.ts'
import { financialLabels } from './reportView.ts'

// Display labels for a backend recommendation. Pure and DOM-free so it can be tested.
// Every number shown here is copied from the backend result; nothing is calculated.

const number = (value: number) => value.toLocaleString('en-IN', { maximumFractionDigits: 1 })

export const TECHNOLOGY_LABEL = { solar: 'Rooftop Solar', wind: 'Small Wind' } as const

export const DECISION_LABEL: Record<SolarDecision, string> = {
  selected: 'Recommended',
  selected_best_available: 'Best available',
  larger_than_needed: 'Larger than needed',
  below_target: 'Below target',
  excluded_infeasible: 'Not feasible',
  excluded_insufficient_data: 'Cannot be checked',
}

export interface RecommendationView {
  recommended: boolean
  technologyLabel: string | null
  capacityLabel: string | null
  generationLabel: string | null
  coverageLabel: string | null
  feasibilityLabel: string | null
  targetNote: string | null
  reason: string
  incentiveLines: string[]
  // The compact yellow (non-error) note shown while verified cost data is unavailable; null once it is available.
  costMessage: string | null
  // Real verified figures, only when cost data is available.
  financials: ReturnType<typeof financialLabels> | null
}

export function recommendationView(result: RecommendationResult): RecommendationView {
  const recommended =
    result.recommendation_status === 'recommended' &&
    result.recommended_technology !== null &&
    result.recommended_capacity_kw !== null

  const incentiveLines = result.applicable_incentives.map((incentive) =>
    incentive.incentive_amount_inr
      ? `${incentive.scheme_name}: ₹${Number(incentive.incentive_amount_inr).toLocaleString('en-IN')}`
      : incentive.scheme_name,
  )

  return {
    recommended,
    technologyLabel: recommended && result.recommended_technology ? TECHNOLOGY_LABEL[result.recommended_technology] : null,
    capacityLabel: recommended && result.recommended_capacity_kw !== null ? `${number(result.recommended_capacity_kw)} kW` : null,
    generationLabel:
      recommended && result.expected_annual_generation_kwh !== null
        ? `${number(result.expected_annual_generation_kwh)} kWh/year`
        : null,
    coverageLabel:
      recommended && result.coverage_percent !== null ? `${number(result.coverage_percent)}% of annual use` : null,
    feasibilityLabel: recommended ? 'Technically feasible' : null,
    targetNote:
      recommended && result.target_met === false
        ? `Does not fully reach the ${number(result.target_coverage_percent)}% target`
        : null,
    reason: result.recommendation_reason,
    incentiveLines,
    costMessage: result.cost_context.status === 'available' ? null : `Technical recommendation. ${result.cost_context.note}`,
    financials: result.cost_context.status === 'available' ? financialLabels(result.cost_context) : null,
  }
}
