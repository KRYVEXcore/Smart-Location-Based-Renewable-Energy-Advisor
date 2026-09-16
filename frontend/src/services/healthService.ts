import { apiGet } from './apiClient'
import type { HealthStatus } from '../types/health'

export function getHealth(): Promise<HealthStatus> {
  return apiGet<HealthStatus>('/api/v1/health')
}
