export type WindCalculationStatus = 'ok' | 'wind_resource_unavailable' | 'location_unavailable' | 'insufficient_data'

export type WindCandidateStatus = 'technically_feasible' | 'marginal' | 'insufficient_resource'

export interface WindCandidate {
  capacity_kw: number
  annual_generation_kwh: number
  monthly_generation_kwh: Record<string, number> | null
  net_capacity_factor: number
  equivalent_full_load_hours: number
  technical_status: WindCandidateStatus
  technical_notes: string[]
}

export interface WindReading {
  reference_height_m: number
  annual_value: number | null
  monthly_values: Record<string, number> | null
  unit: string
}

export interface WindResource {
  provider: string
  period_represented: string | null
  retrieved_at: string
  data_type: string
  readings: WindReading[]
  used_reference_height_m: number
  used_annual_mean_speed_mps: number
  used_monthly_means: boolean
}

export interface WindTurbineModel {
  name: string
  cut_in_speed_mps: number
  rated_speed_mps: number
  cut_out_speed_mps: number
  power_curve: [number, number][]
}

export interface WindAssumption {
  name: string
  value: number
  unit: string
  source: string
  version: string
  effective_from: string
  notes: string
}

export interface WindCalculationResponse {
  status: WindCalculationStatus
  reason: string | null
  assessment_id: string | null
  technology: 'wind'
  resource: WindResource | null
  turbine_model: WindTurbineModel | null
  candidates: WindCandidate[]
  site_space_note: string | null
  assumptions: WindAssumption[]
  limitations: string[]
  methodology: string | null
  calculation_version: string
  assumption_version: string
  calculated_at: string
}
