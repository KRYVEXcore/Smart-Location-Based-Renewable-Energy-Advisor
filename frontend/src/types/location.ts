export interface GeocodingCandidate {
  latitude: number
  longitude: number
  formatted_address: string
  city: string | null
  district: string | null
  state: string | null
  country: string | null
  postal_code: string | null
}

export interface DiscomInfo {
  id: string
  name: string
  short_code: string | null
}

export interface IndiaLocationContext {
  state: string | null
  union_territory: string | null
  district: string | null
  city: string | null
  discom: DiscomInfo | null
  discom_status: 'identified' | 'not_identified' | 'ambiguous'
}

export interface ResourceError {
  code: string
  message: string
}

export interface SolarResourceProfile {
  annual_value: number | null
  monthly_values: Record<string, number> | null
  unit: string
  source: string
  period_represented: string | null
  retrieved_at: string
}

export interface WindSpeedReading {
  reference_height_m: number
  annual_value: number | null
  monthly_values: Record<string, number> | null
  unit: string
}

export interface WindResourceProfile {
  readings: WindSpeedReading[]
  source: string
  period_represented: string | null
  retrieved_at: string
}

export interface WeatherProfile {
  annual_temperature_c: number | null
  monthly_temperature_c: Record<string, number> | null
  annual_precipitation_mm_per_day: number | null
  monthly_precipitation_mm_per_day: Record<string, number> | null
  cloud_index: number | null
  source: string
  period_represented: string | null
  retrieved_at: string
}

export interface ElevationProfile {
  elevation_m: number | null
  source: string
  retrieved_at: string
}

export interface LocationProfile {
  latitude: number
  longitude: number
  formatted_address: string | null
  city: string | null
  state: string | null
  country: string | null
  solar: SolarResourceProfile | null
  wind: WindResourceProfile | null
  weather: WeatherProfile | null
  elevation: ElevationProfile | null
  india: IndiaLocationContext | null
  errors: Record<string, ResourceError>
  retrieved_at: string
}
