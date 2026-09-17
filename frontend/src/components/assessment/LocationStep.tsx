import { useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, LocateFixed, MapPin, Search, X } from 'lucide-react'
import { useGeolocation } from '../../hooks/useGeolocation'
import { useLocationSearch } from '../../hooks/useLocationSearch'
import { getLocationProfile } from '../../services/locationService'
import { ApiError, NetworkError } from '../../services/apiClient'
import { LocationSearchResults } from '../location/LocationSearchResults'
import type { GeocodingCandidate } from '../../types/location'

export interface LocationValue {
  locationQuery: string
  latitude: number | null
  longitude: number | null
  locationCity: string | null
  locationState: string | null
  locationCountry: string | null
}

interface LocationStepProps {
  value: LocationValue
  onChange: (patch: Partial<LocationValue>) => void
}

interface PendingCandidate {
  latitude: number
  longitude: number
  formattedAddress: string
  city: string | null
  district: string | null
  state: string | null
  country: string
}

// Not persisted anywhere — Phase 2's Location model has no district
// column (district/DISCOM are Phase 3-derived, keyed by coordinate, not
// stored per-assessment). It only exists here to show the user what was
// resolved before they confirm.
type Resolution = 'idle' | 'resolving' | 'confirming' | 'not_in_india' | 'error'

function isIndiaCountry(country: string | null): boolean {
  return country?.trim().toLowerCase() === 'india'
}

export function LocationStep({ value, onChange }: LocationStepProps) {
  const { status: geoStatus, error: geoError, locate, reset: resetGeo } = useGeolocation()
  const [resolution, setResolution] = useState<Resolution>('idle')
  const [resolutionError, setResolutionError] = useState<string | null>(null)
  const [pending, setPending] = useState<PendingCandidate | null>(null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const { results, status: searchStatus } = useLocationSearch(value.locationQuery)

  const isConfirmed = value.latitude != null && value.longitude != null

  async function resolveFromCoordinates(latitude: number, longitude: number, fallbackLabel: string) {
    setResolution('resolving')
    setResolutionError(null)
    try {
      const profile = await getLocationProfile(latitude, longitude)
      const resolvedState = profile.india?.state ?? profile.india?.union_territory ?? null
      const country = profile.country
      // Two independent signals, either is enough: Nominatim's own country
      // field, or the state/UT matching India's canonical list (Phase 3).
      // A coordinate with neither is not confidently in India — never
      // silently moved to "the nearest Indian location".
      if (!isIndiaCountry(country) && !resolvedState) {
        setResolution('not_in_india')
        return
      }
      setPending({
        latitude,
        longitude,
        formattedAddress: profile.formatted_address ?? fallbackLabel,
        city: profile.india?.city ?? profile.city ?? null,
        district: profile.india?.district ?? null,
        state: resolvedState,
        country: country ?? 'India',
      })
      setResolution('confirming')
    } catch (err) {
      setResolution('error')
      if (err instanceof NetworkError) {
        setResolutionError('Could not connect to the server. Check your connection and try again.')
      } else if (err instanceof ApiError && err.status >= 500) {
        setResolutionError('Something went wrong while resolving this location. Please try again.')
      } else {
        setResolutionError('Could not resolve this location right now. Try again or search manually.')
      }
    }
  }

  function handleUseCurrentLocation() {
    setIsDropdownOpen(false)
    locate(({ latitude, longitude }) => {
      void resolveFromCoordinates(latitude, longitude, `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`)
    })
  }

  function handleSelectResult(candidate: GeocodingCandidate) {
    setIsDropdownOpen(false)
    if (!isIndiaCountry(candidate.country)) {
      setResolution('not_in_india')
      return
    }
    setPending({
      latitude: candidate.latitude,
      longitude: candidate.longitude,
      formattedAddress: candidate.formatted_address,
      city: candidate.city,
      district: candidate.district,
      state: candidate.state,
      country: candidate.country ?? 'India',
    })
    setResolution('confirming')
  }

  function handleConfirm() {
    if (!pending) return
    onChange({
      locationQuery: pending.formattedAddress,
      latitude: pending.latitude,
      longitude: pending.longitude,
      locationCity: pending.city,
      locationState: pending.state,
      locationCountry: pending.country,
    })
    setResolution('idle')
    setPending(null)
  }

  function handleTryAgain() {
    // Clears the stale query text too — otherwise a fresh search would
    // start by appending to (rather than replacing) whatever was typed
    // before this candidate was abandoned.
    onChange({ locationQuery: '' })
    setResolution('idle')
    setResolutionError(null)
    setPending(null)
    resetGeo()
  }

  function handleChangeLocation() {
    onChange({
      locationQuery: '',
      latitude: null,
      longitude: null,
      locationCity: null,
      locationState: null,
      locationCountry: null,
    })
    handleTryAgain()
  }

  if (isConfirmed) {
    return (
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Where is your building?</h2>
          <p className="mt-1 text-sm text-slate-500">
            Used later to look up local solar and wind resource data.
          </p>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="font-medium text-emerald-900">{value.locationQuery}</p>
            {(value.locationState || value.locationCountry) && (
              <p className="text-sm text-emerald-700">
                {[value.locationState, value.locationCountry].filter(Boolean).join(', ')}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={handleChangeLocation}
            className="flex shrink-0 items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100"
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
            Change
          </button>
        </div>
      </div>
    )
  }

  if (resolution === 'confirming' && pending) {
    return (
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Confirm your location</h2>
          <p className="mt-1 text-sm text-slate-500">Make sure this looks right before continuing.</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <div className="flex items-start gap-3">
            <MapPin className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" aria-hidden="true" />
            <div>
              {pending.city && <p className="text-lg font-semibold text-slate-900">{pending.city}</p>}
              {pending.district && pending.district !== pending.city && (
                <p className="text-sm text-slate-600">{pending.district}</p>
              )}
              {pending.state && <p className="text-sm text-slate-600">{pending.state}</p>}
              <p className="text-sm text-slate-500">{pending.country}</p>
              {!pending.city && (
                <p className="mt-1 text-xs text-slate-400">{pending.formattedAddress}</p>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleTryAgain}
            className="rounded-full border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 hover:border-slate-300"
          >
            Choose a different location
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="flex-1 rounded-full bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            Confirm location
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Where is your building?</h2>
        <p className="mt-1 text-sm text-slate-500">
          Used later to look up local solar and wind resource data.
        </p>
      </div>

      <div className="relative">
        <label htmlFor="location-search" className="sr-only">
          Search your city or address
        </label>
        <Search
          className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          id="location-search"
          type="text"
          value={value.locationQuery}
          onChange={(event) => {
            setIsDropdownOpen(true)
            onChange({ locationQuery: event.target.value, latitude: null, longitude: null })
          }}
          onFocus={() => setIsDropdownOpen(true)}
          onBlur={() => setIsDropdownOpen(false)}
          placeholder="Search your city or address"
          autoComplete="off"
          className="w-full rounded-2xl border border-slate-200 bg-white py-4 pl-12 pr-4 text-base text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
        />
        {isDropdownOpen && <LocationSearchResults results={results} onSelect={handleSelectResult} />}
      </div>
      {searchStatus === 'error' && (
        <p className="text-sm text-amber-600">Search is temporarily unavailable.</p>
      )}

      <button
        type="button"
        onClick={handleUseCurrentLocation}
        disabled={geoStatus === 'locating' || resolution === 'resolving'}
        className="flex items-center justify-center gap-2 self-start rounded-full border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {geoStatus === 'locating' || resolution === 'resolving' ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <LocateFixed className="h-4 w-4" aria-hidden="true" />
        )}
        {geoStatus === 'locating'
          ? 'Detecting your location…'
          : resolution === 'resolving'
            ? 'Resolving location…'
            : 'Use current location'}
      </button>

      {geoStatus === 'error' && geoError && (
        <p role="alert" className="text-sm text-amber-600">
          {geoError}
        </p>
      )}

      {resolution === 'not_in_india' && (
        <p role="alert" className="flex items-start gap-2 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          This assessment currently supports locations in India. Please search for an Indian city or
          address instead.
        </p>
      )}

      {resolution === 'error' && resolutionError && (
        <p role="alert" className="text-sm text-amber-600">
          {resolutionError}
        </p>
      )}
    </div>
  )
}
