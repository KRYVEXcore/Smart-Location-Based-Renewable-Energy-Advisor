import { Mic } from 'lucide-react'

interface FloatingAdvisorButtonProps {
  onClick: () => void
}

export function FloatingAdvisorButton({ onClick }: FloatingAdvisorButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Ask SHREA AI"
      className="fixed bottom-5 right-5 z-20 flex items-center gap-2 rounded-full bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/20 transition-transform hover:scale-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 active:scale-95"
    >
      <Mic className="h-4 w-4" aria-hidden="true" />
      <span className="hidden sm:inline">Ask SHREA AI</span>
    </button>
  )
}
