export type RecommendationStatus = 'recommended' | 'no_suitable_option' | 'insufficient_data'

export type SolarDecision =
  | 'selected'
  | 'selected_best_available'
  | 'larger_than_needed'
  | 'below_target'
  | 'excluded_infeasible'
  | 'excluded_insufficient_data'

export interface EvaluatedSolarOption {
  capacity_kw: number
  annual_generation_kwh: number | null
  coverage_percent: number | null
  technical_status: string
  decision: SolarDecision
  note: string | null
}

export interface ExcludedOption {
  technology: 'solar' | 'wind' | 'hybrid' | 'battery'
  reason_code: string
  reason: string
}

export interface RecommendedIncentive {
  scheme_name: string
  level: string
  incentive_amount_inr: string | null
  calculation_notes: string | null
  effective_from: string | null
  effective_to: string | null
  source_name: string | null
  source_order: string | null
  source_page: string | null
  verification_status: string | null
}

export interface RecommendationResult {
  recommendation_status: RecommendationStatus
  assessment_id: string | null
  recommended_technology: 'solar' | 'wind' | null
  recommended_capacity_kw: number | null
  technical_feasibility: 'technically_feasible' | null
  annual_consumption_kwh: number | null
  expected_annual_generation_kwh: number | null
  coverage_percent: number | null
  target_coverage_percent: number
  target_met: boolean | null
  reason_code: string
  recommendation_reason: string
  solar_options_evaluated: EvaluatedSolarOption[]
  excluded_options: ExcludedOption[]
  applicable_incentives: RecommendedIncentive[]
  incentive_context: { status: string; eligible_programmes: number; note: string } | null
  tariff_context: { status: string; tariff_name: string | null; estimated_monthly_bill_inr: string | null } | null
  // The Financial Analysis Engine's result. status 'available' means a verified COST exists; otherwise the
  // note explains why not (savings may still be present when they could be modelled).
  cost_context: {
    status: 'not_available' | 'available'
    budget_inr: number | null
    note: string
    installed_cost_range_inr?: { low: number; high: number } | null
    incentive_inr?: number | null
    net_investment_range_inr?: { low: number; high: number } | null
    annual_savings_inr?: number | null
    monthly_savings_inr?: number | null
    simple_payback_years_range?: { low: number; high: number } | null
  }
  limitations: string[]
  rules: string[]
  recommendation_version: string
  engine_versions: Record<string, string>
  calculated_at: string
}
