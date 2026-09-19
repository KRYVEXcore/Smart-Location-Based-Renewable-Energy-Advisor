import { Info, Wind } from 'lucide-react'
import type { WindCalculationResponse, WindCandidateStatus } from '../../types/wind'

interface WindAnalysisSectionProps {
  result: WindCalculationResponse
}

const STATUS_LABELS: Record<WindCandidateStatus, string> = {
  technically_feasible: 'Technically feasible',
  marginal: 'Marginal',
  insufficient_resource: 'Insufficient resource',
}

const STATUS_STYLES: Record<WindCandidateStatus, string> = {
  technically_feasible: 'bg-emerald-50 text-emerald-700',
  marginal: 'bg-amber-50 text-amber-700',
  insufficient_resource: 'bg-slate-100 text-slate-500',
}

function EmptyState({ heading, reason }: { heading: string; reason: string | null }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
      <p className="text-sm font-medium text-slate-500">{heading}</p>
      {reason && <p className="mt-1 text-xs text-slate-400">{reason}</p>}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
      <dt className="w-40 shrink-0 text-slate-400">{label}</dt>
      <dd className="min-w-0 break-words text-slate-600">{value}</dd>
    </div>
  )
}

// Technical screening only: never a recommendation, and never a cost/savings
// figure. Every number shown comes from the backend (Phase 3 resource data
// run through the deterministic Wind Engine).
export function WindAnalysisSection({ result }: WindAnalysisSectionProps) {
  if (result.status === 'wind_resource_unavailable') {
    return <EmptyState heading="No verified wind resource is available for this location." reason={result.reason} />
  }
  if (result.status === 'insufficient_data') {
    return (
      <EmptyState
        heading="Wind data is available, but there is not enough information for a reliable technical calculation."
        reason={result.reason}
      />
    )
  }
  if (result.status === 'location_unavailable' || !result.resource) {
    return <EmptyState heading="Wind screening needs a location in India." reason={result.reason} />
  }

  const resource = result.resource
  const statuses = new Set(result.candidates.map((candidate) => candidate.technical_status))
  const first = result.candidates[0]
  const overall = !first ? 'Not available' : statuses.size === 1 ? STATUS_LABELS[first.technical_status] : 'Varies by candidate'

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
      <div className="flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 text-white">
          <Wind className="h-4 w-4" aria-hidden="true" />
        </span>
        <span className="text-lg font-bold text-slate-900">Wind Analysis</span>
      </div>

      <dl className="mt-5 grid gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Resource</dt>
          <dd className="mt-1 text-2xl font-bold text-slate-900">
            {resource.used_annual_mean_speed_mps.toFixed(2)} <span className="text-sm font-medium">m/s</span>
          </dd>
          <dd className="text-xs text-slate-400">Annual mean at {resource.used_reference_height_m} m</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Resource period</dt>
          <dd className="mt-1 text-sm font-medium text-slate-900">
            {resource.period_represented ?? 'Not stated'}
          </dd>
          <dd className="text-xs text-slate-400">Regional climatology, not live wind</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Technical status</dt>
          <dd className="mt-1 text-sm font-medium text-slate-900">{overall}</dd>
          <dd className="text-xs text-slate-400">Under the configured screening model</dd>
        </div>
      </dl>

      <h3 className="mt-6 text-sm font-semibold text-slate-700">Candidate systems</h3>
      <ul className="mt-2 divide-y divide-slate-100 rounded-2xl border border-slate-200">
        {result.candidates.map((candidate) => (
          <li
            key={candidate.capacity_kw}
            className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-3"
          >
            <span className="w-16 text-sm font-bold text-slate-900">{candidate.capacity_kw} kW</span>
            <span className="text-sm font-medium text-slate-900">
              {candidate.annual_generation_kwh.toLocaleString('en-IN')} kWh/year
            </span>
            <span className="text-xs text-slate-400">
              {(candidate.net_capacity_factor * 100).toFixed(1)}% net capacity factor
            </span>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[candidate.technical_status]}`}>
              {STATUS_LABELS[candidate.technical_status]}
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-4 flex items-start gap-2 rounded-xl bg-amber-50 px-4 py-3 text-xs text-amber-700">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        Technical screening only — structural/site approval is required. These are candidate sizes for
        analysis, not a recommendation, and the wind value is a regional model estimate, not a
        measurement at your site.
      </p>

      <details className="mt-4 rounded-2xl border border-slate-200 px-4 py-3 text-xs">
        <summary className="cursor-pointer font-medium text-slate-600">View calculation details</summary>

        <dl className="mt-3 space-y-1.5">
          <Row label="Provider" value={resource.provider} />
          <Row label="Data type" value={resource.data_type} />
          <Row label="Resource period" value={resource.period_represented} />
          <Row label="Retrieved" value={new Date(resource.retrieved_at).toLocaleString('en-IN')} />
          <Row
            label="Readings available"
            value={resource.readings
              .map((r) =>
                r.annual_value != null ? `${r.annual_value.toFixed(2)} ${r.unit} at ${r.reference_height_m} m` : null,
              )
              .filter(Boolean)
              .join(' · ')}
          />
          <Row
            label="Reading used"
            value={`${resource.used_reference_height_m} m (other heights are shown but not used or extrapolated)${
              resource.used_monthly_means ? '; monthly means used' : '; annual mean only'
            }`}
          />
          <Row label="Turbine model" value={result.turbine_model?.name} />
          <Row
            label="Cut-in / rated / cut-out"
            value={
              result.turbine_model
                ? `${result.turbine_model.cut_in_speed_mps} / ${result.turbine_model.rated_speed_mps} / ${result.turbine_model.cut_out_speed_mps} m/s`
                : null
            }
          />
          <Row label="Method" value={result.methodology} />
          <Row label="Assumption version" value={result.assumption_version} />
          <Row label="Site space" value={result.site_space_note} />
        </dl>

        <p className="mt-3 font-medium text-slate-600">Assumptions</p>
        <ul className="mt-1 space-y-1 text-slate-500">
          {result.assumptions.map((assumption) => (
            <li key={assumption.name}>
              <span className="font-medium text-slate-600">
                {assumption.name.replace(/_/g, ' ')}: {assumption.value} {assumption.unit}
              </span>{' '}
              — {assumption.source}
            </li>
          ))}
        </ul>

        <p className="mt-3 font-medium text-slate-600">Limitations</p>
        <ul className="mt-1 list-disc space-y-1 pl-4 text-slate-500">
          {result.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </details>
    </div>
  )
}
