export type BuildingType =
  | 'home'
  | 'school'
  | 'college'
  | 'office'
  | 'shop'
  | 'small_institution'
  | 'other'

export interface BuildingTypeOption {
  value: BuildingType
  label: string
}

export const BUILDING_TYPE_OPTIONS: BuildingTypeOption[] = [
  { value: 'home', label: 'Home' },
  { value: 'school', label: 'School' },
  { value: 'office', label: 'Office' },
  { value: 'shop', label: 'Shop' },
  { value: 'small_institution', label: 'Small Institution' },
]

export interface AssessmentData {
  locationQuery: string
  latitude: number | null
  longitude: number | null
  buildingType: BuildingType | null
  monthlyConsumptionKwh: number
  roofAreaSqft: string
  landAreaSqft: string
  budget: string
  needsBackup: boolean
}

export const INITIAL_ASSESSMENT_DATA: AssessmentData = {
  locationQuery: '',
  latitude: null,
  longitude: null,
  buildingType: null,
  monthlyConsumptionKwh: 300,
  roofAreaSqft: '',
  landAreaSqft: '',
  budget: '',
  needsBackup: false,
}
