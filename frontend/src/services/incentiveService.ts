import { apiPost } from './apiClient'
import type { IncentiveEvaluationResponse } from '../types/incentive'

export function evaluateIncentives(
  assessmentId: string,
  technology: string,
  proposedCapacityKw: number,
): Promise<IncentiveEvaluationResponse> {
  return apiPost<IncentiveEvaluationResponse>('/api/v1/incentives/evaluate', {
    assessment_id: assessmentId,
    technology,
    proposed_capacity_kw: proposedCapacityKw,
  })
}
