import { useCallback, useState } from 'react'
import { evaluateIncentives } from '../services/incentiveService'
import type { IncentiveEvaluationResponse } from '../types/incentive'

export type IncentiveEvaluationStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useIncentiveEvaluation() {
  const [result, setResult] = useState<IncentiveEvaluationResponse | null>(null)
  const [status, setStatus] = useState<IncentiveEvaluationStatus>('idle')

  const runEvaluation = useCallback((assessmentId: string, technology: string, proposedCapacityKw: number) => {
    setStatus('loading')
    evaluateIncentives(assessmentId, technology, proposedCapacityKw)
      .then((data) => {
        setResult(data)
        setStatus('ready')
      })
      .catch(() => {
        setStatus('error')
      })
  }, [])

  return { result, status, runEvaluation }
}
