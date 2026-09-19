import { apiPost } from './apiClient'
import type { WindCalculationResponse } from '../types/wind'

export function calculateWind(assessmentId: string): Promise<WindCalculationResponse> {
  return apiPost<WindCalculationResponse>('/api/v1/wind/calculate', { assessment_id: assessmentId })
}
