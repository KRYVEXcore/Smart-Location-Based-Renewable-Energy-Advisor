import type { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  icon: LucideIcon
  label: string
  value?: string
  unit?: string
  pendingLabel?: string
}

export function MetricCard({ icon: Icon, label, value, unit, pendingLabel }: MetricCardProps) {
  const isPending = value === undefined

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <div className="flex items-center gap-2 text-slate-400">
        <Icon className="h-4 w-4" aria-hidden="true" />
        <span className="text-xs font-semibold uppercase tracking-wide">{label}</span>
      </div>
      {isPending ? (
        <p className="mt-3 text-sm font-medium text-slate-300">
          {pendingLabel ?? 'Awaiting assessment'}
        </p>
      ) : (
        <p className="mt-2 flex items-baseline gap-1.5">
          <span className="text-3xl font-bold tracking-tight text-slate-900">{value}</span>
          {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
        </p>
      )}
    </div>
  )
}
