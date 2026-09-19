// Voice-layer logic tests. They use plain fakes for the browser's recognition and
// speech synthesis, so no microphone, DOM or network is involved and no advisor
// (or NVIDIA) request is ever made. Run with `npm test`.
import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { pickVoice, splitForSpeech, stripMarkdownForSpeech } from '../src/voice/speech.ts'
import {
  createVoiceController,
  VOICE_MESSAGES,
  type RecognitionEventLike,
  type RecognitionLike,
  type SpeechOutput,
  type VoiceView,
} from '../src/voice/voiceController.ts'

class FakeRecognition implements RecognitionLike {
  lang = ''
  continuous = true
  interimResults = false
  maxAlternatives = 0
  onstart: (() => void) | null = null
  onresult: ((event: RecognitionEventLike) => void) | null = null
  onerror: ((event: { error: string }) => void) | null = null
  onend: (() => void) | null = null
  started = false
  stopped = false
  aborted = false
  start() {
    this.started = true
  }
  stop() {
    this.stopped = true
  }
  abort() {
    this.aborted = true
  }
  // Test helpers that mimic what the browser fires.
  begin() {
    this.onstart?.()
  }
  say(transcript: string, isFinal: boolean) {
    this.onresult?.({ resultIndex: 0, results: [{ isFinal, 0: { transcript } }] })
  }
  fail(error: string) {
    this.onerror?.({ error })
  }
  finish() {
    this.onend?.()
  }
}

// Every observable step, in order, so tests can assert what happened inside the user's tap.
const order: string[] = []

class FakeSpeech implements SpeechOutput {
  spoken: string[][] = []
  cancels = 0
  primes = 0
  primeNotice: string | null = null
  prime() {
    this.primes += 1
    order.push('prime')
    return this.primeNotice
  }
  private done: (() => void) | null = null
  private failed: (() => void) | null = null
  speak(chunks: string[], onDone: () => void, onError: () => void) {
    this.spoken.push(chunks)
    this.done = onDone
    this.failed = onError
  }
  cancel() {
    this.cancels += 1
    order.push('cancel')
  }
  finishSpeaking() {
    this.done?.()
  }
  failSpeaking() {
    this.failed?.()
  }
}

function setup(options: { supported?: boolean; speech?: boolean } = {}) {
  order.length = 0
  const recognitions: FakeRecognition[] = []
  const speech = options.speech === false ? null : new FakeSpeech()
  const submitted: string[] = []
  const interim: string[] = []
  const views: VoiceView[] = []
  const controller = createVoiceController({
    createRecognition:
      options.supported === false
        ? null
        : () => {
            const recognition = new FakeRecognition()
            recognitions.push(recognition)
            order.push('recognition-created')
            return recognition
          },
    speech,
    submit: (text) => {
      order.push('submit')
      submitted.push(text)
    },
    onInterim: (text) => interim.push(text),
    onChange: (view) => views.push(view),
  })
  const state = () => views[views.length - 1]?.state
  const current = () => recognitions[recognitions.length - 1] as FakeRecognition
  return { controller, recognitions, speech, submitted, interim, views, state, current }
}

describe('voice conversation', () => {
  it('primes speech synchronously inside the tap, before recognition starts', () => {
    const t = setup()
    t.controller.start()

    // Nothing asynchronous has happened yet: no event fired, no timer, no reply.
    assert.equal(t.speech?.primes, 1)
    assert.deepEqual(order, ['cancel', 'prime', 'recognition-created'])
    assert.ok(order.indexOf('prime') < order.indexOf('recognition-created'))
  })

  it('has primed speech before the advisor request is made', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('How much electricity am I using?', true)

    assert.ok(order.indexOf('prime') < order.indexOf('submit'))
    assert.equal(t.submitted.length, 1)
  })

  it('primes on every explicit tap but creates no advisor request by itself', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.controller.stop()
    t.controller.start()

    assert.equal(t.speech?.primes, 2)
    assert.deepEqual(t.submitted, [])
  })

  it('shows the one-time activation notice the primer reports', () => {
    const t = setup()
    ;(t.speech as FakeSpeech).primeNotice = 'SHREA voice enabled.'
    t.controller.start()

    assert.equal(t.views[t.views.length - 1]?.state, 'requesting_permission')
    assert.equal(t.views[t.views.length - 1]?.message, 'SHREA voice enabled.')
  })

  it('never primes automatically when listening resumes after a reply', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    t.controller.advisorReplied('Answer.')
    t.speech?.finishSpeaking()

    assert.equal(t.recognitions.length, 2)
    assert.equal(t.speech?.primes, 1) // only the tap primed
  })

  it('keeps going if priming throws', () => {
    const t = setup()
    ;(t.speech as FakeSpeech).prime = () => {
      throw new Error('no speech engine')
    }

    assert.doesNotThrow(() => t.controller.start())
    assert.equal(t.recognitions.length, 1)
  })

  it('submits a final transcript exactly once', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('How much electricity am I using?', true)
    t.current().say('How much electricity am I using?', true) // a repeated recognition event
    t.current().finish()

    assert.deepEqual(t.submitted, ['How much electricity am I using?'])
    assert.equal(t.state(), 'processing')
    assert.equal(t.current().stopped, true)
  })

  it('never submits interim results', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('how much', false)
    t.current().say('how much electricity', false)

    assert.deepEqual(t.submitted, [])
    assert.deepEqual(t.interim, ['how much', 'how much electricity'])
    assert.equal(t.state(), 'listening')
  })

  it('ignores an empty transcript', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('   ', true)

    assert.deepEqual(t.submitted, [])
    assert.equal(t.state(), 'idle')
    assert.equal(t.views[t.views.length - 1]?.message, VOICE_MESSAGES.nothingHeard)
  })

  it('stop cancels recognition, speech and the whole session', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    const recognition = t.current()
    t.controller.stop()
    t.controller.advisorReplied('A reply that arrives after Stop.')

    assert.equal(recognition.aborted, true)
    assert.ok((t.speech?.cancels ?? 0) >= 1)
    assert.equal(t.speech?.spoken.length, 0)
    assert.equal(t.state(), 'stopped')
    assert.equal(t.recognitions.length, 1) // nothing restarted the microphone
  })

  it('does not speak an advisor error and does not keep listening', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    t.controller.advisorFailed()

    assert.equal(t.speech?.spoken.length, 0)
    assert.equal(t.state(), 'idle')
    assert.equal(t.recognitions.length, 1)
  })

  it('speaks a successful reply as plain text and then listens again', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    t.controller.advisorReplied('Your usage is **950 kWh** a month.\n- Verified by the app.')

    assert.equal(t.state(), 'speaking')
    assert.deepEqual(t.speech?.spoken[0], ['Your usage is 950 kWh a month. Verified by the app.'])

    t.speech?.finishSpeaking()
    assert.equal(t.recognitions.length, 2)
    assert.equal(t.state(), 'requesting_permission')
    t.current().begin()
    assert.equal(t.state(), 'listening')
  })

  it('only auto-listens while a session the user started is active', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    t.controller.advisorReplied('Answer.')
    t.controller.stop()
    t.speech?.finishSpeaking() // a late "speech ended" after Stop

    assert.equal(t.recognitions.length, 1)
    assert.equal(t.state(), 'stopped')
  })

  it('does not speak replies to typed messages', () => {
    const t = setup()
    t.controller.advisorReplied('A reply to something typed.')

    assert.equal(t.speech?.spoken.length, 0)
    assert.equal(t.views.length, 0) // the voice state is untouched
  })

  it('keeps text chat usable when speech recognition is unsupported', () => {
    const t = setup({ supported: false })

    t.controller.start()
    t.controller.stop()
    t.controller.advisorReplied('text reply')
    t.controller.advisorFailed()

    assert.equal(t.recognitions.length, 0)
    assert.deepEqual(t.submitted, [])
    assert.equal(t.views.length, 0) // no state churn, no errors
  })

  it('starting a new turn cancels earlier speech (barge-in) and ignores its late end', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('first', true)
    t.controller.advisorReplied('A long spoken answer.')
    const cancelsBefore = t.speech?.cancels ?? 0

    t.controller.start() // user presses the microphone while SHREA speaks
    t.speech?.finishSpeaking() // the cancelled speech reports its end late

    assert.ok((t.speech?.cancels ?? 0) > cancelsBefore)
    assert.equal(t.recognitions.length, 2) // exactly one new microphone session
    assert.equal(t.state(), 'requesting_permission')
  })

  it('reports denied microphone permission and ends the session', () => {
    const t = setup()
    t.controller.start()
    t.current().fail('not-allowed')

    assert.equal(t.state(), 'error')
    assert.equal(t.views[t.views.length - 1]?.message, VOICE_MESSAGES.permission)
    assert.equal(t.recognitions.length, 1)
  })

  it('returns to idle after silence instead of looping', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().fail('no-speech')
    t.current().finish()

    assert.equal(t.state(), 'idle')
    assert.equal(t.recognitions.length, 1)
  })

  it('ends the session if the spoken reply fails, leaving the text answer', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    t.controller.advisorReplied('Answer.')
    t.speech?.failSpeaking()

    assert.equal(t.state(), 'error')
    assert.equal(t.views[t.views.length - 1]?.message, VOICE_MESSAGES.playbackUnavailable)
    assert.equal(t.recognitions.length, 1)
  })

  it('survives a speech engine that throws and keeps the text answer', () => {
    const t = setup()
    const speech = t.speech as FakeSpeech
    speech.speak = () => {
      throw new Error('engine exploded')
    }
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)

    assert.doesNotThrow(() => t.controller.advisorReplied('Answer.'))
    assert.equal(t.state(), 'error')
    assert.equal(t.views[t.views.length - 1]?.message, VOICE_MESSAGES.playbackUnavailable)
    assert.equal(t.recognitions.length, 1)
  })

  it('survives a recognition engine that cannot be created', () => {
    const views: VoiceView[] = []
    const controller = createVoiceController({
      createRecognition: () => {
        throw new Error('no engine')
      },
      speech: null,
      submit: () => {},
      onInterim: () => {},
      onChange: (view) => views.push(view),
    })

    assert.doesNotThrow(() => controller.start())
    assert.equal(views[views.length - 1]?.state, 'error')
  })

  it('goes idle after a reply when the browser cannot speak', () => {
    const t = setup({ speech: false })
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    t.controller.advisorReplied('Answer.')

    assert.equal(t.state(), 'idle')
    assert.equal(t.recognitions.length, 1)
  })

  it('cannot start a second turn while the first is still being answered', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    t.current().say('hello', true)
    t.controller.start()

    assert.equal(t.recognitions.length, 1)
    assert.equal(t.state(), 'processing')
  })

  it('dispose releases the microphone and speech without touching the UI', () => {
    const t = setup()
    t.controller.start()
    t.current().begin()
    const recognition = t.current()
    const changes = t.views.length
    t.controller.dispose()

    assert.equal(recognition.aborted, true)
    assert.equal(t.views.length, changes)
  })
})

describe('speech helpers', () => {
  it('strips markdown markers before speaking', () => {
    assert.equal(stripMarkdownForSpeech('## Result\n**Bold** and *soft*\n- item one\n`code`'), 'Result\nBold and soft\nitem one\ncode')
  })

  it('splits long text into sentence-sized chunks', () => {
    const chunks = splitForSpeech('One. Two! Three?', 8)
    assert.deepEqual(chunks, ['One.', 'Two!', 'Three?'])
    assert.deepEqual(splitForSpeech('Short. Text.', 220), ['Short. Text.'])
    assert.deepEqual(splitForSpeech('   ', 220), [])
  })

  it('prefers an English (India) voice, then any English voice, never a fixed name', () => {
    const voices = [{ lang: 'hi-IN' }, { lang: 'en-US' }, { lang: 'en_IN' }]
    assert.equal(pickVoice(voices)?.lang, 'en_IN')
    assert.equal(pickVoice([{ lang: 'fr-FR' }, { lang: 'en-GB' }])?.lang, 'en-GB')
    assert.equal(pickVoice([{ lang: 'fr-FR' }]), undefined)
  })
})
