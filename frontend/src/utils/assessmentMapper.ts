import type { AssessmentData, BuildingType } from '../types/assessment'
import type { AssessmentCreatePayload } from '../types/assessmentApi'

function toNullableNumber(value: string): number | null {
  if (value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function toAssessmentCreatePayload(data: AssessmentData): AssessmentCreatePayload {
  return {
    building: {
      building_type: data.buildingType as BuildingType,
      name: null,
    },
    location: {
      latitude: data.latitude,
      longitude: data.longitude,
      formatted_address: data.locationQuery.trim() === '' ? null : data.locationQuery,
      city: data.locationCity,
      state: data.locationState,
      country: data.locationCountry,
      postal_code: null,
    },
    energy: {
      monthly_consumption_kwh: data.monthlyConsumptionKwh,
    },
    constraints: {
      roof_area_sqft: toNullableNumber(data.roofAreaSqft),
      land_area_sqft: toNullableNumber(data.landAreaSqft),
      budget_inr: toNullableNumber(data.budget),
      backup_required: data.needsBackup,
    },
  }
}
