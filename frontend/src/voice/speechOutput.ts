import { pickVoice, VOICE_LANGUAGE } from './speech.ts'
import type { SpeechOutput } from './voiceController.ts'

// Spoken replies. Kept free of DOM types (the browser objects are injected through
// SpeechEnv) so the mobile-related behaviour can be tested with plain fakes.
//
// Mobile browsers (iOS Safari/WebKit above all) only allow speech that is tied to a
// user gesture, but SHREA speaks after an asynchronous advisor reply. So the
// microphone tap calls prime() synchronously, which starts the speech engine inside
// the gesture. Every real utterance is then checked: if it never starts, the reply is
// reported as not spoken instead of silently hanging.

export interface UtteranceLike {
  lang: string
  voice: unknown
  rate: number
  pitch: number
  volume: number
  onstart: (() => void) | null
  onend: (() => void) | null
  onerror: ((event: { error?: string }) => void) | null
}

export interface SynthLike {
  speaking: boolean
  pending: boolean
  speak(utterance: UtteranceLike): void
  cancel(): void
  getVoices(): readonly { lang: string }[]
}

export interface SpeechEnv {
  synth: SynthLike
  createUtterance(text: string): UtteranceLike
  setTimeout(callback: () => void, ms: number): unknown
  clearTimeout(id: unknown): void
}

// One bounded wait (not polling) for an utterance to actually begin.
export const START_TIMEOUT_MS = 3000
// Only used if the silent primer proved insufficient; spoken at most once per page load.
export const AUDIBLE_ACTIVATION_TEXT = 'SHREA voice enabled.'

export function createSpeechOutput(env: SpeechEnv): SpeechOutput {
  const { synth } = env
  // Internal readiness: true once the engine has been seen to start an utterance.
  let unlocked = false
  let needsAudibleActivation = false
  let audibleTried = false
  // Engines can garbage-collect an utterance that nothing references and then never
  // fire its 'end' event, so whatever is queued is held here.
  let queue: UtteranceLike[] = []
  let startTimer: unknown = null
  // Invalidates callbacks from cancelled or superseded speech.
  let generation = 0

  function clearStartTimer() {
    if (startTimer !== null) {
      env.clearTimeout(startTimer)
      startTimer = null
    }
  }

  function halt() {
    generation += 1
    clearStartTimer()
    queue = []
    // Calling cancel() when nothing is playing can make some engines drop the next speak().
    if (synth.speaking || synth.pending) synth.cancel()
  }

  function makeUtterance(text: string): UtteranceLike {
    const utterance = env.createUtterance(text)
    utterance.lang = VOICE_LANGUAGE
    // Voices load lazily and differ per device; the language above is the fallback.
    const voice = pickVoice(synth.getVoices())
    if (voice) utterance.voice = voice
    utterance.rate = 1
    utterance.pitch = 1
    return utterance
  }

  return {
    // Must run synchronously inside the user's tap, before anything asynchronous.
    prime() {
      synth.getVoices()
      if (unlocked) return null
      const audible = needsAudibleActivation && !audibleTried
      const utterance = makeUtterance(audible ? AUDIBLE_ACTIVATION_TEXT : '')
      if (audible) {
        audibleTried = true
        needsAudibleActivation = false
      } else {
        utterance.volume = 0
      }
      utterance.onstart = utterance.onend = () => {
        unlocked = true
      }
      queue = [utterance]
      synth.speak(utterance)
      return audible ? AUDIBLE_ACTIVATION_TEXT : null
    },

    speak(chunks, onDone, onError) {
      generation += 1
      const mine = generation
      clearStartTimer()
      let started = false
      let failed = false
      let finished = false

      function fail() {
        if (failed || mine !== generation) return
        failed = true
        halt()
        onError()
      }

      queue = chunks.map((chunk, index) => {
        const utterance = makeUtterance(chunk)
        utterance.onstart = () => {
          if (mine !== generation) return
          started = true
          unlocked = true
          clearStartTimer()
        }
        utterance.onerror = (event) => {
          // Cancelling (Stop, barge-in) is expected, not a failure.
          if (event.error === 'canceled' || event.error === 'interrupted') return
          fail()
        }
        if (index === chunks.length - 1) {
          utterance.onend = () => {
            if (mine !== generation || failed || finished) return
            finished = true
            started = true
            unlocked = true
            clearStartTimer()
            onDone()
          }
        }
        return utterance
      })
      for (const utterance of queue) synth.speak(utterance)

      startTimer = env.setTimeout(() => {
        startTimer = null
        if (mine !== generation || started || synth.speaking) return
        // The browser accepted the request but never played it (typically a gesture
        // restriction). Ask for one audible activation on the next tap.
        unlocked = false
        needsAudibleActivation = true
        fail()
      }, START_TIMEOUT_MS)
    },

    cancel() {
      halt()
    },
  }
}
