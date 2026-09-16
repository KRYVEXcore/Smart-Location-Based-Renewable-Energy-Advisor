import type { BuildingType } from './assessment'

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
    monthly_consumption_kwh: number
  }
  constraints: {
    roof_area_sqft: number | null
    land_area_sqft: number | null
    budget_inr: number | null
    backup_required: boolean
  }
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
    monthly_consumption_kwh: number
    annual_consumption_kwh: number | null
  }
  constraints: {
    id: string
    roof_area_sqft: number | null
    land_area_sqft: number | null
    budget_inr: number | null
    backup_required: boolean
  }
}
