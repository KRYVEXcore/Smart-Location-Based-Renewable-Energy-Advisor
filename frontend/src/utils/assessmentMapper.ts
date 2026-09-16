import type { AssessmentData, BuildingType } from '../types/assessment'
import type { AssessmentCreatePayload } from '../types/assessmentApi'

function toNullableNumber(value: string): number | null {
  return value.trim() === '' ? null : Number(value)
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
      city: null,
      state: null,
      country: null,
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
