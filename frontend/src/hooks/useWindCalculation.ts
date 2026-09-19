import { useCallback, useState } from 'react'
import { calculateWind } from '../services/windService'
import type { WindCalculationResponse } from '../types/wind'

export type WindCalculationLoadStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useWindCalculation() {
  const [result, setResult] = useState<WindCalculationResponse | null>(null)
  const [status, setStatus] = useState<WindCalculationLoadStatus>('idle')

  const runCalculation = useCallback((assessmentId: string) => {
    setStatus('loading')
    calculateWind(assessmentId)
      .then((data) => {
        setResult(data)
        setStatus('ready')
      })
      .catch(() => {
        setStatus('error')
      })
  }, [])

  return { result, status, runCalculation }
}
