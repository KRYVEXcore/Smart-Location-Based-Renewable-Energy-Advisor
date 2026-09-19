import { CloudSun, MapPin, Mountain, Sun, Wind } from 'lucide-react'
import { ResourceCard, ResourceMetricRow } from './ResourceCard'
import type { LocationProfile } from '../../types/location'

const DISCOM_STATUS_TEXT = {
  not_identified: 'Not identified',
  ambiguous: 'Several DISCOMs serve this state',
} as const

function LocationSummary({ profile }: { profile: LocationProfile }) {
  const india = profile.india
  const place = india?.city ?? profile.city ?? india?.district ?? profile.formatted_address
  const region = [
    india?.district && india.district !== place ? india.district : null,
    india?.state ?? india?.union_territory ?? profile.state,
    profile.country,
  ]
    .filter(Boolean)
    .join(', ')
  const discom = india?.discom
    ? `${india.discom.name}${india.discom.short_code ? ` (${india.discom.short_code})` : ''}`
    : india
      ? DISCOM_STATUS_TEXT[india.discom_status as keyof typeof DISCOM_STATUS_TEXT]
      : null
  const availability = (loaded: unknown) => (loaded ? 'Available' : 'Unavailable')

  return (
    <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-6">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
          <MapPin className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="break-words text-lg font-semibold text-slate-900">{place ?? 'Selected location'}</p>
          {region && <p className="break-words text-sm text-slate-500">{region}</p>}
        </div>
      </div>
      <dl className="mt-4 grid gap-x-8 gap-y-1 sm:grid-cols-2">
        {[
          ['DISCOM', discom],
          ['Solar', availability(profile.solar)],
          ['Wind', availability(profile.wind)],
          ['Weather', availability(profile.weather)],
          ['Elevation', availability(profile.elevation)],
        ].map(([label, value]) =>
          value ? (
            <div key={label} className="flex flex-wrap items-baseline justify-between gap-x-4 py-1 text-sm">
              <dt className="text-slate-500">{label}</dt>
              <dd className="min-w-0 break-words text-right font-medium text-slate-900">{value}</dd>
            </div>
          ) : null,
        )}
      </dl>
    </div>
  )
}

interface LocationIntelligenceSectionProps {
  profile: LocationProfile
}

export function LocationIntelligenceSection({ profile }: LocationIntelligenceSectionProps) {
  return (
    <div className="flex flex-col gap-4">
      <LocationSummary profile={profile} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ResourceCard
          icon={Sun}
          title="Solar Resource"
          gradient="from-amber-400 to-orange-500"
          error={profile.errors.solar}
        >
          {profile.solar && (
            <>
              <p className="flex flex-wrap items-baseline gap-x-1 text-2xl font-bold text-slate-900">
                {profile.solar.annual_value?.toFixed(2) ?? '—'}
                <span className="text-sm font-medium text-slate-400">{profile.solar.unit}</span>
              </p>
              <p className="text-xs text-slate-400">Annual average</p>
              <div className="mt-3 border-t border-slate-100 pt-2">
                <ResourceMetricRow label="Source" value={profile.solar.source} />
              </div>
            </>
          )}
        </ResourceCard>

        <ResourceCard icon={Wind} title="Wind Resource" gradient="from-sky-400 to-blue-500" error={profile.errors.wind}>
          {profile.wind && (
            <>
              {profile.wind.readings.map((reading) => (
                <ResourceMetricRow
                  key={reading.reference_height_m}
                  label={`At ${reading.reference_height_m}m`}
                  value={
                    reading.annual_value != null
                      ? `${reading.annual_value.toFixed(2)} ${reading.unit}`
                      : '—'
                  }
                />
              ))}
              <div className="mt-2 border-t border-slate-100 pt-2">
                <ResourceMetricRow label="Source" value={profile.wind.source} />
              </div>
            </>
          )}
        </ResourceCard>

        <ResourceCard
          icon={CloudSun}
          title="Weather"
          gradient="from-violet-400 to-fuchsia-500"
          error={profile.errors.weather}
        >
          {profile.weather && (
            <>
              <ResourceMetricRow
                label="Avg. temperature"
                value={
                  profile.weather.annual_temperature_c != null
                    ? `${profile.weather.annual_temperature_c.toFixed(1)} °C`
                    : '—'
                }
              />
              <ResourceMetricRow
                label="Avg. precipitation"
                value={
                  profile.weather.annual_precipitation_mm_per_day != null
                    ? `${profile.weather.annual_precipitation_mm_per_day.toFixed(2)} mm/day`
                    : '—'
                }
              />
              {profile.weather.cloud_index != null && (
                <ResourceMetricRow label="Clearness index" value={profile.weather.cloud_index.toFixed(2)} />
              )}
              <div className="mt-2 border-t border-slate-100 pt-2">
                <ResourceMetricRow label="Source" value={profile.weather.source} />
              </div>
            </>
          )}
        </ResourceCard>

        <ResourceCard
          icon={Mountain}
          title="Elevation"
          gradient="from-emerald-400 to-teal-500"
          error={profile.errors.elevation}
        >
          {profile.elevation && (
            <>
              <p className="flex flex-wrap items-baseline gap-x-1 text-2xl font-bold text-slate-900">
                {profile.elevation.elevation_m != null ? profile.elevation.elevation_m.toFixed(0) : '—'}
                <span className="text-sm font-medium text-slate-400">m</span>
              </p>
              <div className="mt-3 border-t border-slate-100 pt-2">
                <ResourceMetricRow label="Source" value={profile.elevation.source} />
              </div>
            </>
          )}
        </ResourceCard>
      </div>
    </div>
  )
}
