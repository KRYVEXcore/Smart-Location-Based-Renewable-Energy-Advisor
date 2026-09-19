export type IncentiveEvaluationStatus = 'ok' | 'insufficient_data'

export type IncentiveEligibilityStatus =
  | 'eligible'
  | 'not_eligible'
  | 'insufficient_information'
  | 'scheme_expired'
  | 'scheme_not_active'
  | 'scheme_not_verified'
  | 'incentive_data_unavailable'
  | 'discom_not_identified'
  | 'discom_ambiguous'

export type IncentiveLevel = 'central' | 'state' | 'discom'

export interface IncentiveSourceInfo {
  source_name: string | null
  source_url: string | null
  source_document: string | null
  source_order_number: string | null
  source_order_date: string | null
  source_page: string | null
  source_table: string | null
  source_section: string | null
  source_excerpt: string | null
  verification_notes: string | null
  verification_status: 'verified' | 'pending_review' | 'expired' | 'superseded' | 'unavailable' | null
  last_verified: string | null
}

export interface IncentiveEligibilityResult {
  scheme_name: string
  scheme_version: string | null
  level: IncentiveLevel
  incentive_type: string | null
  technology: string
  status: IncentiveEligibilityStatus
  eligible: boolean
  reason: string | null
  missing_fields: string[]
  incentive_amount_inr: string | null
  eligible_cost_basis_inr: string | null
  calculation_notes: string | null
  combination_note: string | null
  source: IncentiveSourceInfo | null
  effective_from: string | null
  effective_to: string | null
}

export interface IncentiveLocationSummary {
  latitude: number
  longitude: number
  formatted_address: string | null
  city: string | null
  district: string | null
  state: string | null
  union_territory: string | null
  country: string | null
  discom_status: 'identified' | 'not_identified' | 'ambiguous'
  discom_name: string | null
}

export interface IncentiveEvaluationSummary {
  verified_programmes: number
  eligible_programmes: number
  calculation_status: 'ok' | 'insufficient_data' | 'no_programmes_found'
}

export interface IncentiveEvaluationResponse {
  status: IncentiveEvaluationStatus
  reason: string | null
  assessment_id: string | null
  technology: string | null
  proposed_capacity_kw: string | null
  location: IncentiveLocationSummary | null
  consumer_category: string | null
  programmes: IncentiveEligibilityResult[]
  summary: IncentiveEvaluationSummary
  calculation_version: string
  calculated_at: string
}
