import { Sun } from 'lucide-react'
import type { SolarSystemOption } from '../../types/solar'

const STATUS_LABELS: Record<string, string> = {
  technically_feasible: 'Technically Feasible',
  technically_infeasible: 'Technically Infeasible',
  insufficient_data: 'Insufficient Data',
}

const STATUS_STYLES: Record<string, string> = {
  technically_feasible: 'bg-emerald-50 text-emerald-700',
  technically_infeasible: 'bg-amber-50 text-amber-700',
  insufficient_data: 'bg-slate-100 text-slate-500',
}

interface SolarOptionCardProps {
  option: SolarSystemOption
}

export function SolarOptionCard({ option }: SolarOptionCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 text-white">
          <Sun className="h-4 w-4" aria-hidden="true" />
        </span>
        <span className="text-lg font-bold text-slate-900">{option.capacity_kw} kW</span>
      </div>

      <dl className="mt-4 space-y-2 text-sm">
        <div className="flex flex-wrap justify-between gap-x-2">
          <dt className="text-slate-500">Generation</dt>
          <dd className="text-right font-medium text-slate-900">
            {option.estimated_annual_generation_kwh != null
              ? `${option.estimated_annual_generation_kwh.toLocaleString()} kWh/yr`
              : '—'}
          </dd>
        </div>
        <div className="flex flex-wrap justify-between gap-x-2">
          <dt className="text-slate-500">Roof Area</dt>
          <dd className="text-right font-medium text-slate-900">
            {option.roof_area_required_sqft.toLocaleString()} sq ft
          </dd>
        </div>
        <div className="flex flex-wrap justify-between gap-x-2">
          <dt className="text-slate-500">Coverage</dt>
          <dd className="text-right font-medium text-slate-900">
            {option.generation_coverage_percent != null ? `${option.generation_coverage_percent}%` : '—'}
          </dd>
        </div>
      </dl>

      <span
        className={`mt-4 block w-fit rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[option.technical_status]}`}
      >
        {STATUS_LABELS[option.technical_status]}
      </span>
      {option.technical_notes.length > 0 && (
        <p className="mt-2 text-xs text-slate-400">{option.technical_notes[0]}</p>
      )}
    </div>
  )
}
