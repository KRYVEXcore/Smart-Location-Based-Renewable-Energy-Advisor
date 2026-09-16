import { Zap } from 'lucide-react'
import { useBackendStatus } from '../../hooks/useBackendStatus'

const STATUS_STYLES: Record<string, string> = {
  checking: 'bg-slate-800 text-slate-300',
  online: 'bg-emerald-500/15 text-emerald-400',
  offline: 'bg-amber-500/15 text-amber-400',
}

const STATUS_LABELS: Record<string, string> = {
  checking: 'Checking backend…',
  online: 'Backend online',
  offline: 'Backend unreachable',
}

export function Footer() {
  const status = useBackendStatus()

  return (
    <footer className="border-t border-white/10 bg-slate-950 text-slate-400">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-6 py-10 text-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-400">
            <Zap className="h-4 w-4" aria-hidden="true" />
          </span>
          <span>Renewable Advisor — SIH 2026 prototype, Phase 1</span>
        </div>
        <span
          className={`w-fit rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLES[status]}`}
        >
          {STATUS_LABELS[status]}
        </span>
      </div>
    </footer>
  )
}
