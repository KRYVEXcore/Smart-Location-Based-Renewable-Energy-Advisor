import { apiPost } from './apiClient'
import type { TariffCalculationResponse } from '../types/tariff'

export function calculateTariff(assessmentId: string): Promise<TariffCalculationResponse> {
  return apiPost<TariffCalculationResponse>('/api/v1/tariffs/calculate', { assessment_id: assessmentId })
}
