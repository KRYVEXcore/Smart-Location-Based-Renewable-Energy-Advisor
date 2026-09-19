import { createSpeechOutput, type SynthLike, type UtteranceLike } from './speechOutput.ts'
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
  return createSpeechOutput({
    synth: window.speechSynthesis as unknown as SynthLike,
    createUtterance: (text) => new SpeechSynthesisUtterance(text) as unknown as UtteranceLike,
    setTimeout: (callback, ms) => window.setTimeout(callback, ms),
    clearTimeout: (id) => window.clearTimeout(id as number),
  })
}
