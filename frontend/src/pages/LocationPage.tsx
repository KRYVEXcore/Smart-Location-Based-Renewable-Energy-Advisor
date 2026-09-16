import { useState } from 'react'
import { LocateFixed, MapPin, Search, Sparkles } from 'lucide-react'
import { Section } from '../components/layout/Section'
import { Button } from '../components/buttons/Button'
import { LocationMap } from '../components/location/LocationMap'
import { LocationSearchResults } from '../components/location/LocationSearchResults'
import { LocationIntelligenceSection } from '../components/location/LocationIntelligenceSection'
import { useGeolocation } from '../hooks/useGeolocation'
import { useLocationSearch } from '../hooks/useLocationSearch'
import { useLocationProfile } from '../hooks/useLocationProfile'
import type { GeocodingCandidate } from '../types/location'

interface SelectedLocation {
  latitude: number
  longitude: number
  formattedAddress: string
}

export function LocationPage() {
  const [query, setQuery] = useState('')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [selected, setSelected] = useState<SelectedLocation | null>(null)
  const { results, status: searchStatus } = useLocationSearch(query)
  const { locate, status: geoStatus, error: geoError } = useGeolocation()
  const { profile, status: profileStatus, fetchProfile } = useLocationProfile()

  function handleSelectResult(candidate: GeocodingCandidate) {
    setIsDropdownOpen(false)
    setQuery(candidate.formatted_address)
    setSelected({
      latitude: candidate.latitude,
      longitude: candidate.longitude,
      formattedAddress: candidate.formatted_address,
    })
  }

  function handleUseCurrentLocation() {
    setIsDropdownOpen(false)
    locate(({ latitude, longitude }) => {
      const label = `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`
      setQuery(label)
      setSelected({ latitude, longitude, formattedAddress: label })
    })
  }

  return (
    <Section width="narrow">
      <h1 className="text-2xl font-bold text-slate-900">Location intelligence</h1>
      <p className="mt-1 text-sm text-slate-500">
        Search a location to see real solar, wind, weather, and elevation data for it.
      </p>

      <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
        <div className="relative">
          <label htmlFor="location-page-search" className="sr-only">
            Search your city or address
          </label>
          <Search
            className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400"
            aria-hidden="true"
          />
          <input
            id="location-page-search"
            type="text"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setIsDropdownOpen(true)
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
          <p className="mt-2 text-sm text-amber-600">Search is temporarily unavailable.</p>
        )}

        <button
          type="button"
          onClick={handleUseCurrentLocation}
          disabled={geoStatus === 'locating'}
          className="mt-4 flex items-center justify-center gap-2 rounded-full border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <LocateFixed className="h-4 w-4" aria-hidden="true" />
          {geoStatus === 'locating' ? 'Locating…' : 'Use current location'}
        </button>
        {geoError && <p className="mt-2 text-sm text-amber-600">{geoError}</p>}
      </div>

      {!selected && (
        <div className="mt-6 flex flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-slate-400 shadow-sm">
            <MapPin className="h-6 w-6" aria-hidden="true" />
          </span>
          <p className="text-sm font-medium text-slate-500">
            Search or use your location above to see the map and resource data.
          </p>
        </div>
      )}

      {selected && (
        <div className="mt-6 flex flex-col gap-6">
          <div className="overflow-hidden rounded-2xl border border-slate-200">
            <LocationMap latitude={selected.latitude} longitude={selected.longitude} />
          </div>

          <div className="flex flex-col items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-700">{selected.formattedAddress}</p>
              <p className="text-xs text-slate-400">
                {selected.latitude.toFixed(4)}, {selected.longitude.toFixed(4)}
              </p>
            </div>
            <Button
              onClick={() => fetchProfile(selected.latitude, selected.longitude)}
              disabled={profileStatus === 'loading'}
            >
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              {profileStatus === 'loading' ? 'Retrieving…' : 'Get Location Intelligence'}
            </Button>
          </div>

          {profileStatus === 'error' && (
            <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
              Location found, but resource data could not be retrieved. Please check your internet
              connection and try again.
            </p>
          )}

          {profile && <LocationIntelligenceSection profile={profile} />}
        </div>
      )}
    </Section>
  )
}
