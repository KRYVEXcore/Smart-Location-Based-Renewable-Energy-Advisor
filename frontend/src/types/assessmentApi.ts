import type { BuildingType } from './assessment.ts'

export type AssessmentStatus = 'draft' | 'submitted' | 'completed'

export interface AssessmentCreatePayload {
  building: {
    building_type: BuildingType
    name: string | null
  }
  location: {
    latitude: number | null
    longitude: number | null
    formatted_address: string | null
    city: string | null
    state: string | null
    country: string | null
    postal_code: string | null
  }
  energy: {
    // The customer's bill is the primary input; units are optional and, when given, authoritative.
    monthly_electricity_bill_inr: number
    monthly_consumption_kwh?: number
  }
  constraints: {
    roof_area_sqft: number | null
    land_area_sqft: number | null
    budget_inr: number | null
    backup_required: boolean
  }
}

export interface ConsumptionEstimate {
  status: 'estimated' | 'insufficient_data'
  reason: string | null
  monthly_bill_inr: number
  estimated_monthly_consumption_kwh: number | null
  range_low_kwh: number | null
  range_high_kwh: number | null
  match: 'within_tolerance' | 'fixed_charge_gap' | null
  method: string
  tariff_name: string | null
  tariff_version: string | null
  limitations: string[]
}

export interface AssessmentResponse {
  id: string
  status: AssessmentStatus
  created_at: string
  updated_at: string
  building: {
    id: string
    building_type: BuildingType
    name: string | null
  }
  location: {
    id: string
    latitude: number | null
    longitude: number | null
    formatted_address: string | null
    city: string | null
    state: string | null
    country: string | null
    postal_code: string | null
  }
  energy: {
    id: string
    // null when a bill-based estimate could not be made (never a default).
    monthly_consumption_kwh: number | null
    annual_consumption_kwh: number | null
    monthly_electricity_bill_inr: number | null
    // 'user_kwh' = entered by the customer; 'user_bill_estimate' = ESTIMATED from the bill.
    consumption_source: 'user_kwh' | 'user_bill_estimate'
    consumption_estimate: ConsumptionEstimate | null
  }
  constraints: {
    id: string
    roof_area_sqft: number | null
    land_area_sqft: number | null
    budget_inr: number | null
    backup_required: boolean
  }
}
