import { apiGet } from './apiClient'
import type { RecommendationResult } from '../types/recommendation'

// Deterministic backend result (no AI involved); SHREA AI only explains it.
export function getRecommendation(assessmentId: string): Promise<RecommendationResult> {
  return apiGet<RecommendationResult>(`/api/v1/recommendations/${assessmentId}`)
}
