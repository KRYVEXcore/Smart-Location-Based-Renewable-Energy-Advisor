import type { LucideIcon } from 'lucide-react'
import { AlertTriangle } from 'lucide-react'
import type { ReactNode } from 'react'
import type { ResourceError } from '../../types/location'

const ERROR_DESCRIPTIONS: Record<string, string> = {
  not_configured: 'This data source is not configured for this deployment.',
  timeout: 'This provider took too long to respond.',
  rate_limited: 'This provider is rate-limited right now — try again shortly.',
  auth_failed: 'This provider rejected the request.',
  invalid_response: 'This provider returned an unexpected response.',
  unavailable: 'This data is currently unavailable.',
}

function describeError(error: ResourceError): string {
  return ERROR_DESCRIPTIONS[error.code] ?? error.message
}

interface ResourceCardProps {
  icon: LucideIcon
  title: string
  gradient: string
  error?: ResourceError
  children?: ReactNode
}

export function ResourceCard({ icon: Icon, title, gradient, error, children }: ResourceCardProps) {
  return (
    <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-6">
      <div className="flex items-center gap-3">
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white`}
        >
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
        <h3 className="min-w-0 break-words font-semibold text-slate-900">{title}</h3>
      </div>
      <div className="mt-4">
        {error ? (
          <div className="flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2.5 text-sm text-amber-700">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="min-w-0 break-words">{describeError(error)}</span>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  )
}

export function ResourceMetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 py-1 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="min-w-0 max-w-full break-words text-right font-medium text-slate-900">{value}</span>
    </div>
  )
}
