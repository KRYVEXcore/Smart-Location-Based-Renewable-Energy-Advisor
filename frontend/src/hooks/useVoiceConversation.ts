import { useEffect, useRef, useState } from 'react'
import { createBrowserSpeechOutput, getRecognitionConstructor } from '../voice/browserSpeech'
import { createVoiceController, VOICE_MESSAGES, type VoiceView } from '../voice/voiceController'
import type { AdvisorChatStatus } from './useAdvisorChat'
import type { ChatMessage } from '../types/advisor'

interface UseVoiceConversationOptions {
  // The existing chat submit: a spoken utterance goes through exactly the same path as typed text.
  send: (text: string) => void
  status: AdvisorChatStatus
  messages: ChatMessage[]
  // Shows interim recognition text in the input box.
  setDraft: (text: string) => void
}

// Wraps the existing chat with voice input and spoken replies. It makes no advisor
// requests itself: it calls `send` once per finished utterance and reacts to the
// chat's own loading -> idle/error transition.
export function useVoiceConversation({ send, status, messages, setDraft }: UseVoiceConversationOptions) {
  const [view, setView] = useState<VoiceView>({ state: 'idle', message: null })
  const previousStatus = useRef(status)
  const [utterance, setUtterance] = useState<{ id: number; text: string } | null>(null)
  const handledUtterance = useRef(0)

  const [controller] = useState(() => {
    const Recognition = getRecognitionConstructor()
    return createVoiceController({
      createRecognition: Recognition ? () => new Recognition() : null,
      speech: createBrowserSpeechOutput(),
      // Handed to the existing `send` by the effect below, so it always uses the current chat state.
      submit: (text) => setUtterance((previous) => ({ id: (previous?.id ?? 0) + 1, text })),
      onInterim: setDraft,
      onChange: setView,
    })
  })

  useEffect(() => {
    if (utterance && handledUtterance.current !== utterance.id) {
      handledUtterance.current = utterance.id
      send(utterance.text)
    }
  }, [utterance, send])
  const supported = getRecognitionConstructor() !== null

  useEffect(() => {
    if (previousStatus.current === 'loading' && status !== 'loading') {
      const last = messages[messages.length - 1]
      if (status === 'idle' && last?.role === 'assistant') controller.advisorReplied(last.text)
      else controller.advisorFailed()
    }
    previousStatus.current = status
  }, [status, messages, controller])

  // Leaving the chat (panel closed, page changed) must release the microphone and silence speech.
  useEffect(() => () => controller.dispose(), [controller])

  return {
    state: supported ? view.state : 'unsupported',
    message: supported ? view.message : VOICE_MESSAGES.unsupported,
    supported,
    start: controller.start,
    stop: controller.stop,
  }
}
