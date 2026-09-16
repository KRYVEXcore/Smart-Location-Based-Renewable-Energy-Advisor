import { apiGet, apiPost } from './apiClient'
import type { AssessmentCreatePayload, AssessmentResponse } from '../types/assessmentApi'

export function createAssessment(payload: AssessmentCreatePayload): Promise<AssessmentResponse> {
  return apiPost<AssessmentResponse>('/api/v1/assessments', payload)
}

export function getAssessment(id: string): Promise<AssessmentResponse> {
  return apiGet<AssessmentResponse>(`/api/v1/assessments/${id}`)
}
