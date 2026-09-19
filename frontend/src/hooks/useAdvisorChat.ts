import { useCallback, useRef, useState } from 'react'
import { AdvisorNotConnectedError, askAdvisor } from '../services/advisorService'

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
}

export type AdvisorChatStatus = 'idle' | 'loading' | 'error'

export function useAdvisorChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<AdvisorChatStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const nextId = useRef(1)

  const send = useCallback((text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return
    setMessages((current) => [...current, { id: nextId.current++, role: 'user', text: trimmed }])
    setStatus('loading')
    setError(null)
    askAdvisor(trimmed)
      .then((reply) => {
        setMessages((current) => [...current, { id: nextId.current++, role: 'assistant', text: reply }])
        setStatus('idle')
      })
      .catch((err: unknown) => {
        setError(
          err instanceof AdvisorNotConnectedError ? err.message : 'SHREA AI could not respond. Please try again.',
        )
        setStatus('error')
      })
  }, [])

  return { messages, status, error, send }
}
