import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { AlertTriangle, Bot, Info, Loader2, Send } from 'lucide-react'
import { useAdvisorChat } from '../../hooks/useAdvisorChat'
import { cn } from '../../utils/cn'

// Chat shell for SHREA AI. It only renders replies that askAdvisor() returns;
// until a real backend exists that call rejects and the UI says so.
export function AdvisorChat({ className }: { className?: string }) {
  const { messages, status, error, send } = useAdvisorChat()
  const [draft, setDraft] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const isLoading = status === 'loading'
  const canSend = draft.trim().length > 0 && !isLoading

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'end' })
  }, [messages, status])

  function submit() {
    if (!canSend) return
    send(draft)
    setDraft('')
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    submit()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <div className={cn('flex min-h-0 flex-col', className)}>
      <div className="flex items-center gap-3 border-b border-slate-200 py-4 pl-5 pr-14">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white">
          <Bot className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h2 className="font-semibold text-slate-900">SHREA AI Advisor</h2>
          <p className="text-xs text-slate-500">Ask about your renewable energy setup.</p>
        </div>
      </div>

      <div role="log" aria-live="polite" aria-label="Conversation" className="min-h-0 flex-1 space-y-3 overflow-y-auto px-5 py-4">
        <p className="flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2.5 text-xs text-amber-700">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          AI Advisor is not connected yet. Replies will appear here once it is.
        </p>

        {messages.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-sm font-medium text-slate-500">No messages yet</p>
            <p className="mt-1 text-xs text-slate-400">Try: &ldquo;How much solar can I install?&rdquo;</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={cn('flex', message.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div
              className={cn(
                'min-w-0 max-w-[85%] rounded-2xl px-4 py-2.5 text-sm',
                message.role === 'user'
                  ? 'rounded-br-md bg-slate-900 text-white'
                  : 'rounded-bl-md border border-slate-200 bg-slate-50 text-slate-800',
              )}
            >
              <p className={cn('text-xs font-semibold', message.role === 'user' ? 'text-slate-300' : 'text-emerald-700')}>
                {message.role === 'user' ? 'You' : 'SHREA AI'}
              </p>
              <p className="mt-0.5 whitespace-pre-wrap break-words">{message.text}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <p className="flex items-center gap-2 text-xs text-slate-500">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            SHREA AI is thinking…
          </p>
        )}
        {status === 'error' && error && (
          <p role="alert" className="flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2.5 text-sm text-amber-700">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="min-w-0 break-words">{error}</span>
          </p>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t border-slate-200 p-4">
        <label htmlFor="advisor-chat-input" className="sr-only">
          Message SHREA AI
        </label>
        <textarea
          id="advisor-chat-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          placeholder="Ask SHREA AI…"
          className="min-w-0 flex-1 resize-none rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
        />
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white transition-colors hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </button>
      </form>
    </div>
  )
}
