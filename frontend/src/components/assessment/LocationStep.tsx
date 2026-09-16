import { useState } from 'react'
import { LocateFixed, Search } from 'lucide-react'
import { useGeolocation } from '../../hooks/useGeolocation'
import { useLocationSearch } from '../../hooks/useLocationSearch'
import { LocationSearchResults } from '../location/LocationSearchResults'
import type { GeocodingCandidate } from '../../types/location'

export interface LocationValue {
  locationQuery: string
  latitude: number | null
  longitude: number | null
}

interface LocationStepProps {
  value: LocationValue
  onChange: (patch: Partial<LocationValue>) => void
}

export function LocationStep({ value, onChange }: LocationStepProps) {
  const { status, error, locate } = useGeolocation()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const { results, status: searchStatus } = useLocationSearch(value.locationQuery)

  function handleUseCurrentLocation() {
    setIsDropdownOpen(false)
    locate(({ latitude, longitude }) => {
      onChange({
        locationQuery: `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`,
        latitude,
        longitude,
      })
    })
  }

  function handleSelectResult(candidate: GeocodingCandidate) {
    setIsDropdownOpen(false)
    onChange({
      locationQuery: candidate.formatted_address,
      latitude: candidate.latitude,
      longitude: candidate.longitude,
    })
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
        disabled={status === 'locating'}
        className="flex items-center justify-center gap-2 self-start rounded-full border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <LocateFixed className="h-4 w-4" aria-hidden="true" />
        {status === 'locating' ? 'Locating…' : 'Use current location'}
      </button>

      {error && <p className="text-sm text-amber-600">{error}</p>}
    </div>
  )
}
