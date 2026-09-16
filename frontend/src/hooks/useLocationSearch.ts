import { useEffect, useRef, useState } from 'react'
import { searchLocations } from '../services/locationService'
import type { GeocodingCandidate } from '../types/location'

const DEBOUNCE_MS = 400
const MIN_QUERY_LENGTH = 3

export type SearchStatus = 'idle' | 'searching' | 'error'

export function useLocationSearch(query: string) {
  const [results, setResults] = useState<GeocodingCandidate[]>([])
  const [status, setStatus] = useState<SearchStatus>('idle')
  const requestIdRef = useRef(0)

  const isQueryTooShort = query.trim().length < MIN_QUERY_LENGTH

  useEffect(() => {
    if (isQueryTooShort) return

    const requestId = ++requestIdRef.current
    setStatus('searching')

    const timeoutId = setTimeout(() => {
      searchLocations(query)
        .then((candidates) => {
          if (requestIdRef.current !== requestId) return
          setResults(candidates)
          setStatus('idle')
        })
        .catch(() => {
          if (requestIdRef.current !== requestId) return
          setStatus('error')
        })
    }, DEBOUNCE_MS)

    return () => clearTimeout(timeoutId)
  }, [query, isQueryTooShort])

  return {
    results: isQueryTooShort ? [] : results,
    status: isQueryTooShort ? 'idle' : status,
  }
}
