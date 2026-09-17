import { Sun } from 'lucide-react'
import { SolarOptionCard } from './SolarOptionCard'
import type { SolarCalculationResponse } from '../../types/solar'

interface SolarAnalysisSectionProps {
  result: SolarCalculationResponse
}

export function SolarAnalysisSection({ result }: SolarAnalysisSectionProps) {
  if (result.status === 'insufficient_data') {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
        <p className="text-sm font-medium text-slate-500">Solar analysis is not available yet.</p>
        {result.reason && <p className="mt-1 text-xs text-slate-400">{result.reason}</p>}
      </div>
    )
  }

  const solarSource = result.data_sources.find((source) => source.category === 'solar_resource')

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-slate-500">
        {solarSource && (
          <span className="flex items-center gap-1.5">
            <Sun className="h-4 w-4" aria-hidden="true" />
            Source: {solarSource.provider}
            {solarSource.period_represented ? ` (${solarSource.period_represented})` : ''}
          </span>
        )}
        {result.annual_consumption_kwh != null && (
          <span>Annual consumption: {result.annual_consumption_kwh.toLocaleString()} kWh</span>
        )}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {result.options.map((option) => (
          <SolarOptionCard key={option.capacity_kw} option={option} />
        ))}
      </div>

      <p className="mt-5 rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-500">
        Financial analysis (cost, subsidies, savings, and payback) will be available in a later
        phase.
      </p>
    </div>
  )
}
