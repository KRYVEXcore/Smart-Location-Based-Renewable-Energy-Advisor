import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { Button } from '../buttons/Button'
import { MONITORED_SYSTEMS } from './monitoredSystems'

interface ConnectSystemDialogProps {
  open: boolean
  onClose: () => void
}

// No device or inverter integration exists yet, so nothing here can be
// selected or connected: the dialog only says which system types are planned.
export function ConnectSystemDialog({ open, onClose }: ConnectSystemDialogProps) {
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    closeRef.current?.focus()

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
        aria-labelledby="connect-system-title"
        onClick={(event) => event.stopPropagation()}
        className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-white p-6 shadow-2xl sm:rounded-3xl"
      >
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
        <h2 id="connect-system-title" className="pr-8 text-xl font-bold text-slate-900">
          Connect your system
        </h2>
        <p className="mt-1 text-sm text-slate-500">Choose your installed system</p>

        <ul className="mt-4 space-y-2">
          {MONITORED_SYSTEMS.map((system) => (
            <li key={system.name} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3">
              <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br ${system.gradient} text-white`}>
                <system.icon className="h-4 w-4" aria-hidden="true" />
              </span>
              <span className="font-medium text-slate-800">{system.name}</span>
            </li>
          ))}
        </ul>

        <p className="mt-4 rounded-xl bg-amber-50 px-3 py-2.5 text-sm text-amber-700">
          Integration support coming soon. No system can be connected yet.
        </p>
        <Button variant="secondary" onClick={onClose} className="mt-5 w-full">
          Close
        </Button>
      </div>
    </div>
  )
}
