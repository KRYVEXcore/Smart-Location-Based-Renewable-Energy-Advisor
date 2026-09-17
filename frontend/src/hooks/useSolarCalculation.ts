import { useCallback, useState } from 'react'
import { calculateSolar } from '../services/solarService'
import type { SolarCalculationResponse } from '../types/solar'

export type SolarCalculationStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useSolarCalculation() {
  const [result, setResult] = useState<SolarCalculationResponse | null>(null)
  const [status, setStatus] = useState<SolarCalculationStatus>('idle')

  const runCalculation = useCallback((assessmentId: string) => {
    setStatus('loading')
    calculateSolar(assessmentId)
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
