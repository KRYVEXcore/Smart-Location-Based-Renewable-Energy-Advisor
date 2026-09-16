import { CloudSun, Mountain, Sun, Wind } from 'lucide-react'
import { ResourceCard, ResourceMetricRow } from './ResourceCard'
import type { LocationProfile } from '../../types/location'

interface LocationIntelligenceSectionProps {
  profile: LocationProfile
}

export function LocationIntelligenceSection({ profile }: LocationIntelligenceSectionProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <ResourceCard
        icon={Sun}
        title="Solar Resource"
        gradient="from-amber-400 to-orange-500"
        error={profile.errors.solar}
      >
        {profile.solar && (
          <>
            <p className="text-2xl font-bold text-slate-900">
              {profile.solar.annual_value?.toFixed(2) ?? '—'}
              <span className="ml-1 text-sm font-medium text-slate-400">{profile.solar.unit}</span>
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
            <p className="text-2xl font-bold text-slate-900">
              {profile.elevation.elevation_m != null ? profile.elevation.elevation_m.toFixed(0) : '—'}
              <span className="ml-1 text-sm font-medium text-slate-400">m</span>
            </p>
            <div className="mt-3 border-t border-slate-100 pt-2">
              <ResourceMetricRow label="Source" value={profile.elevation.source} />
            </div>
          </>
        )}
      </ResourceCard>
    </div>
  )
}
