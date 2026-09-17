import { apiPost } from './apiClient'
import type { SolarCalculationResponse } from '../types/solar'

export function calculateSolar(assessmentId: string): Promise<SolarCalculationResponse> {
  return apiPost<SolarCalculationResponse>('/api/v1/solar/calculate', { assessment_id: assessmentId })
}
