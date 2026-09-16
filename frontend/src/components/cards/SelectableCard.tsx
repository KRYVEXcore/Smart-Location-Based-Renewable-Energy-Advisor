import type { LucideIcon } from 'lucide-react'
import { cn } from '../../utils/cn'

interface SelectableCardProps {
  icon: LucideIcon
  label: string
  selected: boolean
  onClick: () => void
}

export function SelectableCard({ icon: Icon, label, selected, onClick }: SelectableCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        'flex flex-col items-center gap-3 rounded-2xl border-2 px-6 py-8 text-center transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600',
        selected
          ? 'border-emerald-600 bg-emerald-50 shadow-sm'
          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50',
      )}
    >
      <span
        className={cn(
          'flex h-12 w-12 items-center justify-center rounded-xl',
          selected ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-500',
        )}
      >
        <Icon className="h-6 w-6" aria-hidden="true" />
      </span>
      <span className={cn('font-semibold', selected ? 'text-emerald-800' : 'text-slate-700')}>
        {label}
      </span>
    </button>
  )
}
