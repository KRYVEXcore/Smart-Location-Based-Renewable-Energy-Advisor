import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../services/apiClient'
import { askAdvisor, getAdvisorOverview } from '../services/advisorService'
import type { AdvisorOverview, ChatMessage } from '../types/advisor'

export type AdvisorChatStatus = 'idle' | 'loading' | 'error' | 'not_configured'

const HISTORY_SENT = 6

export const NOT_CONNECTED_TEXT = "SHREA AI isn't connected yet."
const GENERIC_ERROR_TEXT = "SHREA AI couldn't process that request. Please try again."
const TOO_MANY_TEXT = 'You are sending messages too quickly. Please wait a moment and try again.'

// Chat state lives here only (short-lived by design); the backend keeps no
// conversation. The overview call builds no AI request, so opening the chat
// costs no AI usage - only submitting a message does, once per message.
export function useAdvisorChat(assessmentId: string | null) {
  const [overview, setOverview] = useState<AdvisorOverview | null>(null)
  const [overviewFailed, setOverviewFailed] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<AdvisorChatStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const nextId = useRef(1)

  useEffect(() => {
    if (!assessmentId) return
    let cancelled = false
    getAdvisorOverview(assessmentId)
      .then((data) => {
        if (!cancelled) setOverview(data)
      })
      .catch(() => {
        if (!cancelled) setOverviewFailed(true)
      })
    return () => {
      cancelled = true
    }
  }, [assessmentId])

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!assessmentId || !trimmed || status === 'loading') return
      const history = messages.slice(-HISTORY_SENT)
      setMessages((current) => [...current, { id: nextId.current++, role: 'user', text: trimmed }])
      setStatus('loading')
      setError(null)
      askAdvisor(assessmentId, trimmed, history)
        .then((response) => {
          if (response.status === 'ok' && response.message) {
            setMessages((current) => [...current, { id: nextId.current++, role: 'assistant', text: response.message as string }])
            setStatus('idle')
          } else if (response.status === 'ai_not_configured') {
            setError(NOT_CONNECTED_TEXT)
            setStatus('not_configured')
          } else {
            setError(GENERIC_ERROR_TEXT)
            setStatus('error')
          }
        })
        .catch((err: unknown) => {
          setError(err instanceof ApiError && err.status === 429 ? TOO_MANY_TEXT : GENERIC_ERROR_TEXT)
          setStatus('error')
        })
    },
    [assessmentId, messages, status],
  )

  return { overview, overviewFailed, messages, status, error, send }
}
