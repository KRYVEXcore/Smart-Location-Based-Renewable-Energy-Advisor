import { useState } from 'react'

type GeolocationStatus = 'idle' | 'locating' | 'error'

export interface Coordinates {
  latitude: number
  longitude: number
}

export function useGeolocation() {
  const [status, setStatus] = useState<GeolocationStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  function locate(onSuccess: (coords: Coordinates) => void) {
    if (!('geolocation' in navigator)) {
      setStatus('error')
      setError('Geolocation is not supported by this browser.')
      return
    }

    setStatus('locating')
    setError(null)

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setStatus('idle')
        onSuccess({ latitude: position.coords.latitude, longitude: position.coords.longitude })
      },
      () => {
        setStatus('error')
        setError('Location permission was denied or is unavailable.')
      },
      { enableHighAccuracy: false, timeout: 10000 },
    )
  }

  return { status, error, locate }
}
