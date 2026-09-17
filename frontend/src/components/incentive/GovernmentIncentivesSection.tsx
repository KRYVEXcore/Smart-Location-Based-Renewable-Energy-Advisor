import { useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  ExternalLink,
  Gift,
  MinusCircle,
  XCircle,
} from 'lucide-react'
import type { IncentiveEligibilityResult, IncentiveEligibilityStatus, IncentiveEvaluationResponse } from '../../types/incentive'

interface GovernmentIncentivesSectionProps {
  result: IncentiveEvaluationResponse
}

const STATUS_BADGE: Record<
  IncentiveEligibilityStatus,
  { icon: typeof CheckCircle2; label: string; className: string }
> = {
  eligible: { icon: CheckCircle2, label: 'Eligible', className: 'bg-emerald-50 text-emerald-700' },
  not_eligible: { icon: XCircle, label: 'Not eligible', className: 'bg-slate-100 text-slate-500' },
  insufficient_information: {
    icon: CircleHelp,
    label: 'More information required',
    className: 'bg-amber-50 text-amber-700',
  },
  scheme_expired: { icon: MinusCircle, label: 'Expired', className: 'bg-slate-100 text-slate-500' },
  scheme_not_active: { icon: MinusCircle, label: 'Not yet active', className: 'bg-slate-100 text-slate-500' },
  scheme_not_verified: {
    icon: AlertTriangle,
    label: 'Verification required',
    className: 'bg-amber-50 text-amber-700',
  },
  incentive_data_unavailable: {
    icon: MinusCircle,
    label: 'No verified programme',
    className: 'bg-slate-100 text-slate-400',
  },
  discom_not_identified: {
    icon: CircleHelp,
    label: 'DISCOM not identified',
    className: 'bg-amber-50 text-amber-700',
  },
  discom_ambiguous: {
    icon: CircleHelp,
    label: 'DISCOM verification required',
    className: 'bg-amber-50 text-amber-700',
  },
}

const LEVEL_LABEL: Record<string, string> = { central: 'Central', state: 'State', discom: 'DISCOM' }

function formatInr(amount: string): string {
  const value = Number(amount)
  return Number.isFinite(value)
    ? `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
    : `₹${amount}`
}

function ProgrammeCard({ programme }: { programme: IncentiveEligibilityResult }) {
  const [expanded, setExpanded] = useState(false)
  const badge = STATUS_BADGE[programme.status]
  const Icon = badge.icon

  return (
    <div className="rounded-2xl border border-slate-200">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              {LEVEL_LABEL[programme.level] ?? programme.level}
            </span>
            <span className="truncate text-sm font-medium text-slate-800">{programme.scheme_name}</span>
          </div>
          {programme.eligible && programme.incentive_amount_inr && (
            <p className="mt-0.5 text-sm font-semibold text-emerald-700">
              {formatInr(programme.incentive_amount_inr)}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${badge.className}`}>
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {badge.label}
          </span>
          <ChevronDown
            className={`h-4 w-4 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </div>
      </button>

      {expanded && (
        <div className="space-y-2 border-t border-slate-100 px-4 py-3 text-sm text-slate-600">
          {programme.reason && <p>{programme.reason}</p>}
          {programme.missing_fields.length > 0 && (
            <p className="text-xs text-slate-400">Missing: {programme.missing_fields.join(', ')}</p>
          )}
          {programme.combination_note && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
              {programme.combination_note === 'mutually_exclusive_with_other_programme'
                ? 'This programme may not be combinable with another eligible programme shown here.'
                : 'Whether this programme can be combined with another eligible one shown here has not been verified.'}
            </p>
          )}
          {(programme.effective_from || programme.effective_to) && (
            <p className="text-xs text-slate-400">
              Effective: {programme.effective_from ?? '—'} – {programme.effective_to ?? 'ongoing'}
            </p>
          )}
          {programme.source?.source_name && (
            <p className="text-xs text-slate-400">
              Source: {programme.source.source_name}
              {programme.source.last_verified ? ` (verified ${programme.source.last_verified})` : ''}
            </p>
          )}
          {programme.source?.source_url && (
            <a
              href={programme.source.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 hover:underline"
            >
              Official source <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          )}
        </div>
      )}
    </div>
  )
}

export function GovernmentIncentivesSection({ result }: GovernmentIncentivesSectionProps) {
  if (result.status === 'insufficient_data') {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
        <p className="text-sm font-medium text-slate-500">Government incentive data is not available yet.</p>
        {result.reason && <p className="mt-1 text-xs text-slate-400">{result.reason}</p>}
      </div>
    )
  }

  if (result.programmes.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
        <p className="text-sm font-medium text-slate-500">
          No verified incentive programme is configured for this location.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-slate-500">
        <span className="flex items-center gap-1.5">
          <Gift className="h-4 w-4" aria-hidden="true" />
          {result.technology} • {result.consumer_category?.replace(/_/g, ' ')}
        </span>
        {result.location?.formatted_address && <span>{result.location.formatted_address}</span>}
      </div>

      <div className="mt-5 space-y-3">
        {result.programmes.map((programme) => (
          <ProgrammeCard key={`${programme.level}-${programme.scheme_name}`} programme={programme} />
        ))}
      </div>

      <p className="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-500">
        This is an estimate based on verified, configured programme rules — it does not guarantee that a
        utility, government agency, or vendor will approve an application. Final installation cost, savings,
        and payback are not part of this estimate and will be available in a later phase.
      </p>
    </div>
  )
}
