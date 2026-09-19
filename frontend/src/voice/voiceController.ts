import { splitForSpeech, stripMarkdownForSpeech, VOICE_LANGUAGE } from './speech.ts'

// Voice is only an input/output layer around the existing advisor chat: it turns a
// finished utterance into text for the normal chat submit, and speaks the normal reply.
// It has no access to the advisor API, keys or audio storage. Kept free of DOM types
// so the state machine can be tested with plain fakes.

export type VoiceState =
  | 'idle'
  | 'requesting_permission'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'stopped'
  | 'unsupported'
  | 'error'

export interface VoiceView {
  state: VoiceState
  message: string | null
}

export interface RecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  onstart: (() => void) | null
  onresult: ((event: RecognitionEventLike) => void) | null
  onerror: ((event: { error: string }) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}

export interface RecognitionEventLike {
  resultIndex: number
  results: ArrayLike<{ isFinal: boolean; [index: number]: { transcript: string } | undefined }>
}

export interface SpeechOutput {
  speak(chunks: string[], onDone: () => void, onError: () => void): void
  cancel(): void
}

export interface VoiceDeps {
  // null when the browser has no speech recognition; text chat is unaffected.
  createRecognition: (() => RecognitionLike) | null
  // null when the browser cannot speak; replies stay visible as text.
  speech: SpeechOutput | null
  // Hands a finished utterance to the existing chat submit (one advisor request).
  submit: (text: string) => void
  // Shows what is being heard in the input box. Never submitted.
  onInterim: (text: string) => void
  onChange: (view: VoiceView) => void
}

export const VOICE_MESSAGES = {
  unsupported: "Voice input isn't supported in this browser. You can still type.",
  permission: 'Microphone permission is required for voice input. You can still type.',
  noMicrophone: 'No microphone was found. You can still type.',
  network: 'Voice recognition is unavailable right now (it needs an internet connection). You can still type.',
  failed: 'Voice input failed. You can still type or try again.',
  nothingHeard: "I didn't catch that. Tap the microphone to try again.",
  speechFailed: "Couldn't play the spoken reply. The answer is shown above; tap the microphone to try again.",
} as const

export function createVoiceController(deps: VoiceDeps) {
  let state: VoiceState = deps.createRecognition ? 'idle' : 'unsupported'
  // True only between the user pressing the microphone and stopping or ending the session.
  // Automatic re-listening happens only while it is true, so there is no unbounded mic loop.
  let sessionActive = false
  // A voice utterance was submitted and its advisor reply is pending; replies to typed
  // messages are never spoken.
  let awaitingReply = false
  let recognition: RecognitionLike | null = null
  // Invalidates callbacks from an earlier recognition or utterance (barge-in, stop).
  let epoch = 0

  function set(next: VoiceState, message: string | null = null) {
    state = next
    deps.onChange({ state, message })
  }

  function endSession(next: VoiceState, message: string | null = null) {
    release()
    sessionActive = false
    awaitingReply = false
    set(next, message)
  }

  function release() {
    epoch += 1
    const current = recognition
    recognition = null
    if (current) {
      current.onstart = current.onresult = current.onerror = current.onend = null
      try {
        current.abort()
      } catch {
        // already stopped
      }
    }
  }

  function listen() {
    if (!deps.createRecognition) return
    const id = ++epoch
    let submitted = false
    let rec: RecognitionLike
    try {
      rec = deps.createRecognition()
    } catch {
      endSession('error', VOICE_MESSAGES.failed)
      return
    }
    rec.lang = VOICE_LANGUAGE
    rec.continuous = false
    rec.interimResults = true
    rec.maxAlternatives = 1
    recognition = rec

    rec.onstart = () => {
      if (id === epoch) set('listening')
    }
    rec.onresult = (event) => {
      if (id !== epoch || submitted) return
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i]
        const transcript = result?.[0]?.transcript ?? ''
        if (result?.isFinal) final += transcript
        else interim += transcript
      }
      if (final) {
        submitted = true
        deps.onInterim('')
        const text = final.trim()
        if (!text) {
          endSession('idle', VOICE_MESSAGES.nothingHeard)
          return
        }
        set('processing')
        awaitingReply = true
        try {
          rec.stop()
        } catch {
          // already stopped
        }
        deps.submit(text)
      } else if (interim) {
        deps.onInterim(interim.trim())
      }
    }
    rec.onerror = (event) => {
      if (id !== epoch) return
      deps.onInterim('')
      switch (event.error) {
        case 'aborted':
          return
        case 'not-allowed':
        case 'service-not-allowed':
          endSession('error', VOICE_MESSAGES.permission)
          return
        case 'no-speech':
          endSession('idle', VOICE_MESSAGES.nothingHeard)
          return
        case 'audio-capture':
          endSession('error', VOICE_MESSAGES.noMicrophone)
          return
        case 'network':
          endSession('error', VOICE_MESSAGES.network)
          return
        default:
          endSession('error', VOICE_MESSAGES.failed)
      }
    }
    rec.onend = () => {
      // Ended without a final result (and without an error event): nothing to submit.
      if (id !== epoch || (state !== 'listening' && state !== 'requesting_permission')) return
      deps.onInterim('')
      endSession('idle', VOICE_MESSAGES.nothingHeard)
    }

    try {
      rec.start()
    } catch {
      endSession('error', VOICE_MESSAGES.failed)
    }
  }

  return {
    // Microphone pressed. Also the barge-in: it silences SHREA and starts listening.
    start() {
      if (!deps.createRecognition || state === 'processing') return
      release()
      deps.speech?.cancel()
      sessionActive = true
      awaitingReply = false
      set('requesting_permission')
      listen()
    },

    // Stop pressed: ends the session, drops the microphone and silences speech.
    stop() {
      if (!deps.createRecognition) return
      release()
      deps.speech?.cancel()
      deps.onInterim('')
      endSession('stopped')
    },

    // The existing chat received a reply to the utterance we submitted.
    advisorReplied(text: string) {
      if (!awaitingReply) return
      awaitingReply = false
      if (!sessionActive || state !== 'processing') return
      const chunks = splitForSpeech(stripMarkdownForSpeech(text))
      if (!deps.speech || chunks.length === 0) {
        endSession('idle')
        return
      }
      const id = ++epoch
      set('speaking')
      try {
        deps.speech.speak(
          chunks,
          () => {
            if (id !== epoch || !sessionActive || state !== 'speaking') return
            set('requesting_permission')
            listen()
          },
          () => {
            if (id !== epoch) return
            endSession('error', VOICE_MESSAGES.speechFailed)
          },
        )
      } catch {
        // A speech engine that throws must never take the chat down; the text answer stays visible.
        endSession('error', VOICE_MESSAGES.speechFailed)
      }
    },

    // The existing chat could not answer (API error, not configured, rate limit).
    // The error is shown by the chat itself and is never spoken.
    advisorFailed() {
      if (!awaitingReply) return
      endSession('idle')
    },

    // Component unmounted: release the microphone and speech without notifying the UI.
    dispose() {
      release()
      deps.speech?.cancel()
      sessionActive = false
      awaitingReply = false
    },
  }
}

export type VoiceController = ReturnType<typeof createVoiceController>
