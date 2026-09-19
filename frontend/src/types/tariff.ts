export type TariffDataStatus = 'ok' | 'insufficient_data' | 'tariff_not_configured' | 'discom_ambiguous'

export type ChargeComponentName = 'energy' | 'fixed' | 'demand' | 'wheeling' | 'tod'
export type ChargeComponentStatus = 'included' | 'not_included' | 'not_calculated'

export interface TariffChargeComponent {
  component: ChargeComponentName
  status: ChargeComponentStatus
  // A decimal string (e.g. "1234.50"), never a float — see the backend's
  // Decimal-only money-math rule.
  amount_inr: string | null
  notes: string | null
}

export interface TariffLocationSummary {
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

export interface TariffScheduleSummary {
  tariff_name: string
  tariff_version: string
  consumer_category: string
  effective_from: string
  effective_to: string | null
  source_url: string | null
  source_document: string | null
  source_name: string | null
  source_order_number: string | null
  source_order_date: string | null
  source_page: string | null
  source_table: string | null
  source_section: string | null
  source_excerpt: string | null
  verification_notes: string | null
  last_verified: string | null
  verification_status: 'verified' | 'pending_review' | 'expired' | 'superseded' | 'unavailable' | null
}

export interface TariffCalculationResponse {
  status: TariffDataStatus
  reason: string | null
  location: TariffLocationSummary | null
  consumer_category: string | null
  tariff: TariffScheduleSummary | null
  monthly_consumption_kwh: string | null
  charges: TariffChargeComponent[]
  estimated_monthly_bill_inr: string | null
  is_partial_estimate: boolean
  excluded_components: string[]
  calculation_version: string
  calculated_at: string
}
