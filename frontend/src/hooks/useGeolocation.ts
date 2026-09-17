import { useState } from 'react'

// The Geolocation API gives no separate callback for "the browser's native
// permission prompt is showing" vs. "permission was already granted and
// the device is now acquiring a fix" — both happen inside the single call
// below, so both are represented as 'locating' here rather than inventing
// a distinction the browser doesn't actually expose.
export type GeolocationStatus = 'idle' | 'locating' | 'error'

export interface Coordinates {
  latitude: number
  longitude: number
  accuracy: number
}

const TIMEOUT_MS = 15_000

function messageForError(error: GeolocationPositionError): string {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      return 'Location access was denied. You can search for a location instead.'
    case error.POSITION_UNAVAILABLE:
      return "Your device couldn't determine the location. Try again or search manually."
    case error.TIMEOUT:
      return 'Location detection took too long. Try again or search manually.'
    default:
      return 'Could not determine your location. Try again or search manually.'
  }
}

export function useGeolocation() {
  const [status, setStatus] = useState<GeolocationStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  function locate(onSuccess: (coords: Coordinates) => void, onError?: () => void) {
    if (!('geolocation' in navigator)) {
      setStatus('error')
      setError('Geolocation is not supported by this browser. Try searching for a location instead.')
      onError?.()
      return
    }

    setStatus('locating')
    setError(null)

    // A single, fresh snapshot — never watchPosition (no continuous
    // tracking), and maximumAge: 0 so a stale cached fix from earlier in
    // the browser session is never reused for a request the user just
    // explicitly made "now".
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setStatus('idle')
        onSuccess({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        })
      },
      (positionError) => {
        setStatus('error')
        setError(messageForError(positionError))
        onError?.()
      },
      { enableHighAccuracy: true, timeout: TIMEOUT_MS, maximumAge: 0 },
    )
  }

  function reset() {
    setStatus('idle')
    setError(null)
  }

  return { status, error, locate, reset }
}
