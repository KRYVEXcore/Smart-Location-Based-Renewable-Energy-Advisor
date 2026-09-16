import { MapPin } from 'lucide-react'
import type { GeocodingCandidate } from '../../types/location'

interface LocationSearchResultsProps {
  results: GeocodingCandidate[]
  onSelect: (candidate: GeocodingCandidate) => void
}

export function LocationSearchResults({ results, onSelect }: LocationSearchResultsProps) {
  if (results.length === 0) return null

  return (
    <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg">
      {results.map((candidate, index) => (
        <li key={index}>
          <button
            type="button"
            // Fires before the input's onBlur closes the dropdown.
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => onSelect(candidate)}
            className="flex w-full items-start gap-2 px-4 py-3 text-left text-sm hover:bg-slate-50"
          >
            <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
            <span className="text-slate-700">{candidate.formatted_address}</span>
          </button>
        </li>
      ))}
    </ul>
  )
}
