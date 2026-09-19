import { CheckCircle2, Info, Sparkles, Sun, Wind } from 'lucide-react'
import type { RecommendationResult } from '../../types/recommendation'
import { DECISION_LABEL, recommendationView } from '../../utils/recommendationView'

// The recommendation is produced by the backend's deterministic Recommendation Engine
// (no AI). This card only displays it; SHREA AI can then explain it in chat.
export function RecommendationCard({ result }: { result: RecommendationResult }) {
  const view = recommendationView(result)
  const Icon = result.recommended_technology === 'wind' ? Wind : Sun

  if (!view.recommended) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6 sm:p-8">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          SHREA recommendation
        </p>
        <p className="mt-3 text-lg font-semibold text-slate-800">No system can be recommended yet</p>
        <p className="mt-1 break-words text-sm text-slate-600">{view.reason}</p>
      </div>
    )
  }

  return (
    <div className="min-w-0 overflow-hidden rounded-3xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-white p-6 shadow-sm sm:p-8">
      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-emerald-700">
        <Sparkles className="h-4 w-4" aria-hidden="true" />
        SHREA recommendation
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-4">
        <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 text-white">
          <Icon className="h-7 w-7" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="text-lg font-semibold text-slate-900">{view.technologyLabel}</p>
          <p className="text-5xl font-bold tracking-tight text-slate-900">{view.capacityLabel}</p>
        </div>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Expected generation</dt>
          <dd className="mt-0.5 text-lg font-semibold text-slate-900">{view.generationLabel}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-slate-400">Annual coverage</dt>
          <dd className="mt-0.5 text-lg font-semibold text-slate-900">{view.coverageLabel}</dd>
        </div>
      </dl>

      <p className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800">
        <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
        {view.feasibilityLabel}
      </p>
      {view.targetNote && <p className="mt-2 text-sm font-medium text-amber-700">{view.targetNote}</p>}

      <h3 className="mt-5 text-sm font-semibold text-slate-700">Why this solution?</h3>
      <p className="mt-1 break-words text-sm text-slate-600">{view.reason}</p>

      {view.incentiveLines.length > 0 && (
        <p className="mt-3 break-words text-sm text-slate-600">
          <span className="font-semibold text-slate-700">Verified incentive: </span>
          {view.incentiveLines.join('; ')}
        </p>
      )}

      <p className="mt-3 flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2.5 text-xs text-amber-700">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        <span className="min-w-0 break-words">
          Technical recommendation. {view.costNote}
        </span>
      </p>

      <details className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs">
        <summary className="cursor-pointer font-medium text-slate-600">View details</summary>

        {result.solar_options_evaluated.length > 0 && (
          <div className="mt-3">
            <p className="font-medium text-slate-600">Solar sizes evaluated</p>
            <ul className="mt-1 divide-y divide-slate-100">
              {result.solar_options_evaluated.map((option) => (
                <li key={option.capacity_kw} className="flex flex-wrap justify-between gap-x-3 py-1.5 text-slate-600">
                  <span className="font-medium text-slate-800">{option.capacity_kw} kW</span>
                  <span>{option.coverage_percent !== null ? `${option.coverage_percent}% coverage` : '—'}</span>
                  <span className="text-slate-500">{DECISION_LABEL[option.decision]}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="mt-3 font-medium text-slate-600">Not recommended</p>
        <ul className="mt-1 space-y-1 text-slate-500">
          {result.excluded_options.map((option) => (
            <li key={option.technology} className="break-words">
              <span className="font-medium capitalize text-slate-600">{option.technology}:</span> {option.reason}
            </li>
          ))}
        </ul>

        <p className="mt-3 font-medium text-slate-600">Limitations</p>
        <ul className="mt-1 list-disc space-y-1 pl-4 text-slate-500">
          {result.limitations.map((limitation) => (
            <li key={limitation} className="break-words">
              {limitation}
            </li>
          ))}
        </ul>

        <p className="mt-3 font-medium text-slate-600">How it was chosen</p>
        <ol className="mt-1 list-decimal space-y-1 pl-4 text-slate-500">
          {result.rules.map((rule) => (
            <li key={rule} className="break-words">
              {rule.replace(/^\d+\.\s*/, '')}
            </li>
          ))}
        </ol>
        <p className="mt-2 text-slate-400">Version {result.recommendation_version}</p>
      </details>
    </div>
  )
}
