import { useCallback, useState } from 'react'
import { getLocationProfile } from '../services/locationService'
import type { LocationProfile } from '../types/location'

export type ProfileStatus = 'idle' | 'loading' | 'ready' | 'error'

export function useLocationProfile() {
  const [profile, setProfile] = useState<LocationProfile | null>(null)
  const [status, setStatus] = useState<ProfileStatus>('idle')

  const fetchProfile = useCallback((latitude: number, longitude: number) => {
    setStatus('loading')
    getLocationProfile(latitude, longitude)
      .then((data) => {
        setProfile(data)
        setStatus('ready')
      })
      .catch(() => {
        setStatus('error')
      })
  }, [])

  return { profile, status, fetchProfile }
}
