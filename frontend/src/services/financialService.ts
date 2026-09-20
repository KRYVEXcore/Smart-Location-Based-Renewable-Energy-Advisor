import { apiGet } from './apiClient'
import type { FinancialAnalysisResult } from '../types/financial'

// Deterministic backend result (no AI involved); SHREA AI only explains it.
export function getFinancialAnalysis(assessmentId: string): Promise<FinancialAnalysisResult> {
  return apiGet<FinancialAnalysisResult>(`/api/v1/financial-analysis/${assessmentId}`)
}
