import { Landmark, PiggyBank, TrendingUp } from 'lucide-react'
import type { RecommendationResult } from '../../types/recommendation'
import { NOT_AVAILABLE, costSavingsView } from '../../utils/reportView'

function Stat({ label, value }: { label: string; value: string }) {
  const available = value !== NOT_AVAILABLE
  return (
    <div className="min-w-0">
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className={`mt-1 break-words text-lg font-semibold ${available ? 'text-slate-900' : 'text-slate-300'}`}>{value}</dd>
    </div>
  )
}

// Cost breakdown and savings, in the customer report. Every figure must come from a
// deterministic engine; until the Financial Analysis Engine exists these read "Not available".
export function ReportFinancialSection({ recommendation }: { recommendation: RecommendationResult | null }) {
  const view = costSavingsView(recommendation)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
        <p className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <Landmark className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          Cost breakdown
        </p>
        <dl className="mt-4 grid gap-4">
          <Stat label="Installed cost" value={view.installedCost} />
          <div className="min-w-0">
            <dt className="text-xs uppercase tracking-wide text-slate-400">Verified incentive</dt>
            {view.incentiveLines.length > 0 ? (
              view.incentiveLines.map((line) => (
                <dd key={line} className="mt-1 break-words text-lg font-semibold text-slate-900">
                  {line}
                </dd>
              ))
            ) : (
              <dd className="mt-1 text-lg font-semibold text-slate-300">None verified</dd>
            )}
          </div>
          <Stat label="Estimated net investment" value={view.netInvestment} />
        </dl>
        <p className="mt-4 break-words text-xs text-slate-500">{view.basisNote}</p>
      </div>

      <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
        <p className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <PiggyBank className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          Estimated savings
        </p>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <Stat label="Estimated annual savings" value={view.annualSavings} />
          <Stat label="Estimated monthly savings" value={view.monthlySavings} />
        </dl>
        <p className="mt-4 flex items-center gap-2 text-sm font-semibold text-slate-800">
          <TrendingUp className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          Estimated simple payback
        </p>
        <p className={`mt-1 text-lg font-semibold ${view.payback === NOT_AVAILABLE ? 'text-slate-300' : 'text-slate-900'}`}>
          {view.payback}
        </p>
        <p className="mt-4 text-xs text-slate-500">{view.financingNote}</p>
      </div>
    </div>
  )
}
