import { useCallback, useState } from 'react'
import { getRecommendation } from '../services/recommendationService'
import type { RecommendationResult } from '../types/recommendation'

export type RecommendationLoadStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useRecommendation() {
  const [result, setResult] = useState<RecommendationResult | null>(null)
  const [status, setStatus] = useState<RecommendationLoadStatus>('idle')

  const runRecommendation = useCallback((assessmentId: string) => {
    setStatus('loading')
    getRecommendation(assessmentId)
      .then((data) => {
        setResult(data)
        setStatus('ready')
      })
      .catch(() => {
        setStatus('error')
      })
  }, [])

  return { result, status, runRecommendation }
}
