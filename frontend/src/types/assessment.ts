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
  { value: 'college', label: 'College' },
  { value: 'office', label: 'Office' },
  { value: 'shop', label: 'Shop' },
  { value: 'small_institution', label: 'Small Institution' },
  { value: 'other', label: 'Other' },
]

export interface AssessmentData {
  locationQuery: string
  latitude: number | null
  longitude: number | null
  // Populated from the confirmed geocoding/reverse-geocoding result (see
  // LocationStep) — never hand-typed, so these always describe the same
  // point as latitude/longitude.
  locationCity: string | null
  locationState: string | null
  locationCountry: string | null
  buildingType: BuildingType | null
  // Typed as text so an empty field is empty (never a fabricated default): the bill is the
  // primary input, and units (kWh) are optional.
  monthlyBillInr: string
  monthlyUnitsKwh: string
  roofAreaSqft: string
  landAreaSqft: string
  budget: string
  needsBackup: boolean
}

export const INITIAL_ASSESSMENT_DATA: AssessmentData = {
  locationQuery: '',
  latitude: null,
  longitude: null,
  locationCity: null,
  locationState: null,
  locationCountry: null,
  buildingType: null,
  monthlyBillInr: '',
  monthlyUnitsKwh: '',
  roofAreaSqft: '',
  landAreaSqft: '',
  budget: '',
  needsBackup: false,
}
