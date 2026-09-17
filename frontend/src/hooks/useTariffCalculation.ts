import { useCallback, useState } from 'react'
import { calculateTariff } from '../services/tariffService'
import type { TariffCalculationResponse } from '../types/tariff'

export type TariffCalculationStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useTariffCalculation() {
  const [result, setResult] = useState<TariffCalculationResponse | null>(null)
  const [status, setStatus] = useState<TariffCalculationStatus>('idle')

  const runCalculation = useCallback((assessmentId: string) => {
    setStatus('loading')
    calculateTariff(assessmentId)
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
