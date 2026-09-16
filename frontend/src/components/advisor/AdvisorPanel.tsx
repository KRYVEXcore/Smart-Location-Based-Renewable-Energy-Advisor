import { useEffect } from 'react'
import { X } from 'lucide-react'
import { AdvisorExperience } from './AdvisorExperience'

interface AdvisorPanelProps {
  open: boolean
  onClose: () => void
}

export function AdvisorPanel({ open, onClose }: AdvisorPanelProps) {
  useEffect(() => {
    if (!open) return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/40 backdrop-blur-sm sm:items-center"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="advisor-panel-title"
        onClick={(event) => event.stopPropagation()}
        className="relative w-full max-w-md rounded-t-3xl bg-white shadow-2xl sm:rounded-3xl"
      >
        <h2 id="advisor-panel-title" className="sr-only">
          AI Energy Advisor
        </h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close advisor"
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
        >
          <X className="h-4 w-4" />
        </button>
        <AdvisorExperience />
      </div>
    </div>
  )
}
