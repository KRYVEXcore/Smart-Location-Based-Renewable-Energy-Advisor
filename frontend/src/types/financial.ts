export type FinancialStatus = 'complete' | 'cost_unavailable' | 'savings_unavailable' | 'insufficient_data' | 'not_applicable'

export interface Range {
  low: number
  high: number
}

export interface CostBasis {
  record_id: string
  cost_kind: string
  name: string
  source_name: string
  source_document: string
  source_url: string
  source_page: string
  source_section: string
  effective_from: string
  capacity_basis: string
  geographic_scope: string
  inclusions: string
  exclusions: string
  gst_treatment: string
  verification_status: string
  last_verified: string
}

// Deterministic backend result (no AI). A value the backend could not support is null, never 0.
export interface FinancialAnalysisResult {
  status: FinancialStatus
  reason: string | null
  assessment_id: string | null
  technology: 'solar' | 'wind' | null
  capacity_kw: number | null
  cost_status: 'available' | 'not_available'
  gross_cost_range_inr: Range | null
  cost_basis: CostBasis | null
  incentive_inr: number | null
  incentive_scheme: string | null
  incentive_note: string | null
  net_investment_range_inr: Range | null
  savings_status: 'available' | 'not_available'
  annual_savings_inr: number | null
  monthly_savings_inr: number | null
  baseline_annual_bill_inr: number | null
  annual_bill_after_solar_inr: number | null
  annual_self_consumed_kwh: number | null
  annual_surplus_generation_kwh: number | null
  tariff_name: string | null
  tariff_version: string | null
  simple_payback_years_range: Range | null
  payback_note: string | null
  methodology: string[]
  limitations: string[]
  calculation_version: string
  calculated_at: string
}
