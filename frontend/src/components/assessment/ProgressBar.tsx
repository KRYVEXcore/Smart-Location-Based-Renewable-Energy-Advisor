interface ProgressBarProps {
  current: number
  total: number
  label: string
}

export function ProgressBar({ current, total, label }: ProgressBarProps) {
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="font-semibold text-slate-900">
          STEP {current} OF {total}
        </span>
        <span className="text-slate-500">{label}</span>
      </div>
      <div className="mt-3 flex gap-1.5" role="progressbar" aria-valuenow={current} aria-valuemin={1} aria-valuemax={total}>
        {Array.from({ length: total }, (_, index) => (
          <span
            key={index}
            className={`h-1.5 flex-1 rounded-full ${index < current ? 'bg-emerald-600' : 'bg-slate-200'}`}
          />
        ))}
      </div>
    </div>
  )
}
