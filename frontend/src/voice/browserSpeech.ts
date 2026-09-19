import { pickVoice, VOICE_LANGUAGE } from './speech.ts'
import type { RecognitionLike, SpeechOutput } from './voiceController.ts'

// Browser glue for the Web Speech API. Recognition uses whatever service the browser
// provides and yields text only; no audio is recorded, stored or uploaded by this app.

type RecognitionConstructor = new () => RecognitionLike

export function getRecognitionConstructor(): RecognitionConstructor | null {
  const speechWindow = window as unknown as {
    SpeechRecognition?: RecognitionConstructor
    webkitSpeechRecognition?: RecognitionConstructor
  }
  return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null
}

export function createBrowserSpeechOutput(): SpeechOutput | null {
  if (typeof window === 'undefined' || !('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
    return null
  }
  const synth = window.speechSynthesis

  return {
    speak(chunks, onDone, onError) {
      synth.cancel()
      // Voices load lazily and differ per device; the utterance language is a fallback
      // when none has loaded yet.
      const voice = pickVoice(synth.getVoices())
      let failed = false
      chunks.forEach((chunk, index) => {
        const utterance = new SpeechSynthesisUtterance(chunk)
        utterance.lang = VOICE_LANGUAGE
        if (voice) utterance.voice = voice
        utterance.rate = 1
        utterance.pitch = 1
        utterance.onerror = (event) => {
          // Cancelling (Stop, barge-in) is expected, not a failure.
          if (failed || event.error === 'canceled' || event.error === 'interrupted') return
          failed = true
          synth.cancel()
          onError()
        }
        if (index === chunks.length - 1) utterance.onend = () => !failed && onDone()
        synth.speak(utterance)
      })
    },
    cancel() {
      synth.cancel()
    },
  }
}
