import { apiGet, apiPost } from './apiClient'
import type { AssessmentCreatePayload, AssessmentResponse } from '../types/assessmentApi'

export function createAssessment(payload: AssessmentCreatePayload): Promise<AssessmentResponse> {
  return apiPost<AssessmentResponse>('/api/v1/assessments', payload)
}

// Bill-first assessments: retry deriving the kWh estimate (for example after a provider hiccup).
export function estimateConsumption(id: string): Promise<AssessmentResponse> {
  return apiPost<AssessmentResponse>(`/api/v1/assessments/${id}/estimate-consumption`, {})
}

export function getAssessment(id: string): Promise<AssessmentResponse> {
  return apiGet<AssessmentResponse>(`/api/v1/assessments/${id}`)
}
