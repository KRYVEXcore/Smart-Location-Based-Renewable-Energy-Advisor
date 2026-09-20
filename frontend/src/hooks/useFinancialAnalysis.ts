import { useCallback, useState } from 'react'
import { getFinancialAnalysis } from '../services/financialService'
import type { FinancialAnalysisResult } from '../types/financial'

export type FinancialLoadStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useFinancialAnalysis() {
  const [result, setResult] = useState<FinancialAnalysisResult | null>(null)
  const [status, setStatus] = useState<FinancialLoadStatus>('idle')

  const runFinancialAnalysis = useCallback((assessmentId: string) => {
    setStatus('loading')
    getFinancialAnalysis(assessmentId)
      .then((data) => {
        setResult(data)
        setStatus('ready')
      })
      .catch(() => {
        setStatus('error')
      })
  }, [])

  return { result, status, runFinancialAnalysis }
}
