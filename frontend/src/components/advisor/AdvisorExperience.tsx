import { Mic, Sparkles } from 'lucide-react'
import { ADVISOR_STATE_LABELS, type AdvisorState } from '../../types/advisor'

const STATE_ORDER: AdvisorState[] = ['ready', 'listening', 'processing', 'responding']

interface AdvisorExperienceProps {
  state?: AdvisorState
}

export function AdvisorExperience({ state = 'ready' }: AdvisorExperienceProps) {
  return (
    <div className="flex flex-col items-center px-6 py-10 text-center">
      <span className="mb-6 inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        AI Energy Advisor
      </span>

      <div className="relative mb-6 flex h-28 w-28 items-center justify-center">
        <span className="absolute inset-0 animate-ping rounded-full bg-emerald-400/20" />
        <span className="absolute inset-2 rounded-full bg-emerald-400/10" />
        <span className="relative flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 text-slate-400">
          <Mic className="h-7 w-7" aria-hidden="true" />
        </span>
      </div>

      <h2 className="text-2xl font-bold text-slate-900">Ask about your energy.</h2>
      <p className="mt-2 max-w-sm text-sm text-slate-500">
        Voice and AI-powered answers are being built in a future phase. The interface below shows
        how the conversation will look once it&apos;s connected.
      </p>

      <div className="mt-6 flex w-full max-w-sm items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm text-slate-400">
        <Mic className="h-4 w-4 shrink-0" aria-hidden="true" />
        <span className="truncate">Ask about your energy…</span>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
        {STATE_ORDER.map((item) => (
          <span
            key={item}
            className={
              item === state
                ? 'rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white'
                : 'rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-400'
            }
          >
            {ADVISOR_STATE_LABELS[item]}
          </span>
        ))}
      </div>
    </div>
  )
}
