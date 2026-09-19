import { useEffect, useRef, useState } from 'react'
import { createBrowserSpeechOutput, getRecognitionConstructor } from '../voice/browserSpeech'
import { splitForSpeech, VOICE_LANGUAGE } from '../voice/speech'
import { VOICE_MESSAGES, type RecognitionLike } from '../voice/voiceController'
import { interpretBillUtterance } from '../utils/billInput'

// Say the bill instead of typing it. Recognition only produces text; the app parses and
// validates it (utils/billInput.ts). No advisor/AI request is made, and no audio is stored.
export function useVoiceBillInput(onAmount: (amount: number) => void) {
  const [listening, setListening] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [confirmation, setConfirmation] = useState<string | null>(null)
  const [speech] = useState(() => createBrowserSpeechOutput())
  const recognition = useRef<RecognitionLike | null>(null)
  const supported = getRecognitionConstructor() !== null

  useEffect(
    () => () => {
      recognition.current?.abort()
      speech?.cancel()
    },
    [speech],
  )

  function stop() {
    recognition.current?.abort()
    setListening(false)
  }

  function start() {
    const Recognition = getRecognitionConstructor()
    if (!Recognition) return
    // Still inside the tap: mobile browsers only allow speech tied to a gesture.
    speech?.cancel()
    try {
      speech?.prime()
    } catch {
      // best effort
    }
    setMessage(null)
    setConfirmation(null)

    const rec = new Recognition()
    rec.lang = VOICE_LANGUAGE
    rec.continuous = false
    rec.interimResults = false
    rec.maxAlternatives = 1
    rec.onstart = () => setListening(true)
    rec.onresult = (event) => {
      const transcript = event.results[event.results.length - 1]?.[0]?.transcript ?? ''
      const outcome = interpretBillUtterance(transcript)
      if (outcome.kind === 'amount') {
        onAmount(outcome.amount)
        setConfirmation(outcome.confirmation)
        speech?.speak(splitForSpeech(outcome.confirmation), () => {}, () => {})
      } else {
        setMessage(outcome.message)
      }
    }
    rec.onerror = (event) => {
      if (event.error === 'aborted') return
      setMessage(
        event.error === 'not-allowed' || event.error === 'service-not-allowed'
          ? VOICE_MESSAGES.permission
          : event.error === 'no-speech'
            ? VOICE_MESSAGES.nothingHeard
            : VOICE_MESSAGES.failed,
      )
    }
    rec.onend = () => setListening(false)
    recognition.current = rec
    try {
      rec.start()
    } catch {
      setMessage(VOICE_MESSAGES.failed)
    }
  }

  return { supported, listening, message, confirmation, start, stop }
}
