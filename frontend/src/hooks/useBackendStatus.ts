import { useEffect, useState } from 'react'
import { getHealth } from '../services/healthService'

export type BackendStatus = 'checking' | 'online' | 'offline'

export function useBackendStatus(): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>('checking')

  useEffect(() => {
    let cancelled = false

    getHealth()
      .then(() => {
        if (!cancelled) setStatus('online')
      })
      .catch(() => {
        if (!cancelled) setStatus('offline')
      })

    return () => {
      cancelled = true
    }
  }, [])

  return status
}
