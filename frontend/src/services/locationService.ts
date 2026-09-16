import { apiGet } from './apiClient'
import type { GeocodingCandidate, LocationProfile } from '../types/location'

export function searchLocations(query: string, limit = 5): Promise<GeocodingCandidate[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) })
  return apiGet<GeocodingCandidate[]>(`/api/v1/locations/search?${params.toString()}`)
}

export function getLocationProfile(latitude: number, longitude: number): Promise<LocationProfile> {
  const params = new URLSearchParams({ latitude: String(latitude), longitude: String(longitude) })
  return apiGet<LocationProfile>(`/api/v1/locations/profile?${params.toString()}`)
}
