export type TechnicalStatus = 'technically_feasible' | 'technically_infeasible' | 'insufficient_data'

export interface SolarSystemOption {
  capacity_kw: number
  estimated_annual_generation_kwh: number | null
  estimated_monthly_generation_kwh: Record<string, number> | null
  roof_area_required_sqft: number
  generation_coverage_percent: number | null
  technical_status: TechnicalStatus
  technical_notes: string[]
}

export interface SolarAssumption {
  name: string
  value: number
  unit: string
  source: string
  version: string
  effective_from: string
  notes: string
}

export interface SolarDataSource {
  category: 'solar_resource' | 'location'
  provider: string
  unit: string | null
  period_represented: string | null
  retrieved_at: string | null
}

export interface SolarLocationSummary {
  latitude: number
  longitude: number
  formatted_address: string | null
  city: string | null
  district: string | null
  state: string | null
  union_territory: string | null
  country: string | null
  discom_status: 'identified' | 'not_identified' | 'ambiguous'
}

export interface SolarCalculationResponse {
  status: 'ok' | 'insufficient_data'
  reason: string | null
  location: SolarLocationSummary | null
  consumer_category: string | null
  technology: 'solar'
  annual_consumption_kwh: number | null
  options: SolarSystemOption[]
  assumptions: SolarAssumption[]
  data_sources: SolarDataSource[]
  calculation_version: string
  assumption_version: string
  calculated_at: string
}
