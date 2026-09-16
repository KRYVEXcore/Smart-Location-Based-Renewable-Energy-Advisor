import type { LucideIcon } from 'lucide-react'

const ROWS = ['Suitability', 'Capacity', 'Cost', 'Savings', 'Payback']

interface ComparisonCardProps {
  icon: LucideIcon
  name: string
  gradient: string
}

export function ComparisonCard({ icon: Icon, name, gradient }: ComparisonCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      <div className="flex items-center gap-3">
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white`}
        >
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
        <h3 className="font-semibold text-slate-900">{name}</h3>
      </div>
      <dl className="mt-5 divide-y divide-slate-100 border-t border-slate-100">
        {ROWS.map((row) => (
          <div key={row} className="py-2.5">
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{row}</dt>
            <dd className="mt-0.5 text-sm font-medium text-slate-300">Awaiting assessment</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
