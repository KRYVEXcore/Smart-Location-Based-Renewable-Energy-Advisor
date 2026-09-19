import type { AssessmentData, BuildingType } from '../types/assessment.ts'
import type { AssessmentCreatePayload } from '../types/assessmentApi.ts'
import { validateMonthlyBill, validateOptionalUnits } from './billInput.ts'

function toNullableNumber(value: string): number | null {
  if (value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function toAssessmentCreatePayload(data: AssessmentData): AssessmentCreatePayload {
  const bill = validateMonthlyBill(data.monthlyBillInr)
  const units = validateOptionalUnits(data.monthlyUnitsKwh)
  if (!bill.ok) throw new Error(bill.message)
  if (!units.ok) throw new Error(units.message)

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
    // The bill is always sent; units only when the customer chose to enter them.
    energy: {
      monthly_electricity_bill_inr: bill.value,
      ...(units.value !== null ? { monthly_consumption_kwh: units.value } : {}),
    },
    constraints: {
      roof_area_sqft: toNullableNumber(data.roofAreaSqft),
      land_area_sqft: toNullableNumber(data.landAreaSqft),
      budget_inr: toNullableNumber(data.budget),
      backup_required: data.needsBackup,
    },
  }
}
