import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, Bot, Info, Loader2, Send } from 'lucide-react'
import { NOT_CONNECTED_TEXT, useAdvisorChat } from '../../hooks/useAdvisorChat'
import { cn } from '../../utils/cn'

interface AdvisorChatProps {
  assessmentId: string | null
  className?: string
}

// SHREA AI chat. Replies come only from POST /api/v1/advisor/chat, where the
// backend builds the assessment context from its own verified results. Model
// output is rendered as plain text (React escapes it); it is never parsed as HTML.
export function AdvisorChat({ assessmentId, className }: AdvisorChatProps) {
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

      {assessmentId ? (
        <AssessmentChat key={assessmentId} assessmentId={assessmentId} />
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-10 text-center">
          <p className="text-sm text-slate-500">
            SHREA AI answers questions about a specific assessment. Open an assessment dashboard, then ask from there.
          </p>
          <Link
            to="/assess"
            className="rounded-full bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
          >
            Start an assessment
          </Link>
        </div>
      )}
    </div>
  )
}

function AssessmentChat({ assessmentId }: { assessmentId: string }) {
  const { overview, overviewFailed, messages, status, error, send } = useAdvisorChat(assessmentId)
  const [draft, setDraft] = useState('')
  const logRef = useRef<HTMLDivElement>(null)
  const isLoading = status === 'loading'
  const notConnected = overview?.ai_configured === false || status === 'not_configured'
  const canSend = draft.trim().length > 0 && !isLoading && !notConnected

  useEffect(() => {
    // Scrolls the chat box itself, never the page.
    const log = logRef.current
    if (log) log.scrollTop = log.scrollHeight
  }, [messages, status])

  function submit(text: string) {
    if (isLoading || notConnected || !text.trim()) return
    send(text)
    setDraft('')
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    submit(draft)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit(draft)
    }
  }

  const contextLine = overview
    ? [
        overview.location_label,
        overview.building_type.replace(/_/g, ' '),
        overview.monthly_consumption_kwh != null ? `${overview.monthly_consumption_kwh} kWh/month` : null,
      ]
        .filter(Boolean)
        .join(' · ')
    : null

  return (
    <>
      {contextLine && (
        <p className="break-words border-b border-slate-100 bg-slate-50 px-5 py-2 text-xs text-slate-500">
          <span className="font-medium text-slate-600">Assessment:</span> {contextLine}
        </p>
      )}

      <div
        ref={logRef}
        role="log"
        aria-live="polite"
        aria-label="Conversation"
        className="min-h-0 flex-1 space-y-3 overflow-y-auto px-5 py-4"
      >
        {notConnected && (
          <p className="flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2.5 text-sm text-amber-700">
            <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            {NOT_CONNECTED_TEXT} AI service configuration is required on the server.
          </p>
        )}
        {overviewFailed && (
          <p className="flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2.5 text-sm text-amber-700">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            This assessment could not be loaded, so SHREA AI cannot answer about it right now.
          </p>
        )}

        {messages.length === 0 && !notConnected && (
          <div className="py-6 text-center">
            <p className="text-sm font-medium text-slate-500">Ask SHREA AI about your energy assessment.</p>
          </div>
        )}

        {messages.length === 0 && !notConnected && overview && (
          <div className="flex flex-wrap justify-center gap-2">
            {overview.suggested_questions.map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => submit(question)}
                disabled={isLoading}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:opacity-50"
              >
                {question}
              </button>
            ))}
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
          maxLength={1000}
          disabled={notConnected}
          placeholder={notConnected ? NOT_CONNECTED_TEXT : 'Ask SHREA AI…'}
          className="min-w-0 flex-1 resize-none rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:bg-slate-50"
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
    </>
  )
}
