// Speech output tests with a mocked speech engine and a manual timer: no browser,
// audio device, advisor request or NVIDIA call is involved. Run with `npm test`.
import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import {
  AUDIBLE_ACTIVATION_TEXT,
  createSpeechOutput,
  START_TIMEOUT_MS,
  type SynthLike,
  type UtteranceLike,
} from '../src/voice/speechOutput.ts'

class FakeUtterance implements UtteranceLike {
  lang = ''
  voice: unknown = null
  rate = 0
  pitch = 0
  volume = 1
  onstart: (() => void) | null = null
  onend: (() => void) | null = null
  onerror: ((event: { error?: string }) => void) | null = null
  text: string
  constructor(text: string) {
    this.text = text
  }
}

function setup(voices: { lang: string }[] = []) {
  const events: string[] = []
  const spoken: FakeUtterance[] = []
  const timers: { id: number; callback: () => void; ms: number }[] = []
  let nextTimer = 1
  const synth: SynthLike & { cancelCalls: number } = {
    speaking: false,
    pending: false,
    cancelCalls: 0,
    speak(utterance) {
      spoken.push(utterance as FakeUtterance)
      events.push(`speak:${(utterance as FakeUtterance).text}`)
    },
    cancel() {
      this.cancelCalls += 1
      events.push('cancel')
    },
    getVoices() {
      events.push('getVoices')
      return voices
    },
  }
  const output = createSpeechOutput({
    synth,
    createUtterance: (text) => new FakeUtterance(text),
    setTimeout: (callback, ms) => {
      const id = nextTimer++
      // A timer that has fired is no longer pending.
      timers.push({
        id,
        ms,
        callback: () => {
          const index = timers.findIndex((timer) => timer.id === id)
          if (index >= 0) timers.splice(index, 1)
          callback()
        },
      })
      return id
    },
    clearTimeout: (id) => {
      const index = timers.findIndex((timer) => timer.id === id)
      if (index >= 0) timers.splice(index, 1)
    },
  })
  return { output, synth, spoken, timers, events }
}

describe('priming inside the user gesture', () => {
  it('loads voices and speaks a silent empty utterance', () => {
    const t = setup([{ lang: 'en-IN' }])
    const notice = t.output.prime()

    assert.equal(notice, null) // no confirmation is spoken or shown
    assert.deepEqual(t.events, ['getVoices', 'getVoices', 'speak:'])
    assert.equal(t.spoken[0]?.text, '')
    assert.equal(t.spoken[0]?.volume, 0)
    assert.equal(t.spoken[0]?.lang, 'en-IN')
  })

  it('stops priming once the engine has been seen to start', () => {
    const t = setup()
    t.output.prime()
    t.spoken[0]?.onstart?.()
    t.output.prime()
    t.output.prime()

    assert.equal(t.spoken.length, 1) // one primer only
  })

  it('does not call cancel when nothing is playing (avoids dropping the next utterance)', () => {
    const t = setup()
    t.output.cancel()
    t.output.prime()

    assert.equal(t.synth.cancelCalls, 0)
  })

  it('cancels speech that is actually playing or queued', () => {
    const t = setup()
    t.synth.speaking = true
    t.output.cancel()
    t.synth.speaking = false
    t.synth.pending = true
    t.output.cancel()

    assert.equal(t.synth.cancelCalls, 2)
  })
})

describe('spoken replies', () => {
  it('speaks the chunks in order with the preferred voice, and reports the end once', () => {
    const t = setup([{ lang: 'hi-IN' }, { lang: 'en-IN' }])
    let done = 0
    let failed = 0
    t.output.speak(['One.', 'Two.'], () => (done += 1), () => (failed += 1))

    assert.deepEqual(t.spoken.map((u) => u.text), ['One.', 'Two.'])
    assert.equal((t.spoken[0]?.voice as { lang: string } | undefined)?.lang, 'en-IN')
    assert.equal(t.spoken[0]?.rate, 1)
    assert.equal(t.spoken[0]?.pitch, 1)
    assert.equal(t.synth.cancelCalls, 0) // no cancel() glued in front of speak()

    t.spoken[0]?.onstart?.()
    t.spoken[0]?.onend?.() // first chunk ending is not the end of the reply
    assert.equal(done, 0)
    t.spoken[1]?.onend?.()
    t.spoken[1]?.onend?.()
    assert.equal(done, 1)
    assert.equal(failed, 0)
    assert.equal(t.timers.length, 0) // the start check was cleared
  })

  it('reports the reply as not spoken if it never starts, without long polling', () => {
    const t = setup()
    let done = 0
    let failed = 0
    t.output.speak(['A reply.'], () => (done += 1), () => (failed += 1))

    assert.equal(t.timers.length, 1)
    assert.equal(t.timers[0]?.ms, START_TIMEOUT_MS)
    t.timers[0]?.callback()

    assert.equal(failed, 1)
    assert.equal(done, 0)
    assert.equal(t.timers.length, 0) // one bounded wait, no repeats
  })

  it('treats a speaking engine as started even if no start event arrived', () => {
    const t = setup()
    let failed = 0
    t.output.speak(['A reply.'], () => {}, () => (failed += 1))
    t.synth.speaking = true
    t.timers[0]?.callback()

    assert.equal(failed, 0)
  })

  it('reports an engine error once', () => {
    const t = setup()
    let failed = 0
    t.output.speak(['One.', 'Two.'], () => {}, () => (failed += 1))
    t.spoken[0]?.onerror?.({ error: 'synthesis-failed' })
    t.spoken[1]?.onerror?.({ error: 'synthesis-failed' })

    assert.equal(failed, 1)
  })

  it('does not treat cancellation as a failure', () => {
    const t = setup()
    let failed = 0
    t.output.speak(['One.'], () => {}, () => (failed += 1))
    t.spoken[0]?.onerror?.({ error: 'canceled' })
    t.spoken[0]?.onerror?.({ error: 'interrupted' })

    assert.equal(failed, 0)
  })

  it('cancel (Stop / barge-in) silences it and ignores every late event', () => {
    const t = setup()
    let done = 0
    let failed = 0
    t.output.speak(['One.'], () => (done += 1), () => (failed += 1))
    t.synth.speaking = true
    t.output.cancel()

    assert.equal(t.synth.cancelCalls, 1)
    assert.equal(t.timers.length, 0) // the pending start check is gone
    t.spoken[0]?.onstart?.()
    t.spoken[0]?.onend?.()
    t.spoken[0]?.onerror?.({ error: 'synthesis-failed' })
    assert.equal(done + failed, 0)
  })

  it('a newer reply supersedes an older one', () => {
    const t = setup()
    let firstDone = 0
    t.output.speak(['Old.'], () => (firstDone += 1), () => {})
    const old = t.spoken[0]
    t.output.speak(['New.'], () => {}, () => {})
    old?.onend?.()

    assert.equal(firstDone, 0)
  })
})

describe('one-time audible activation fallback', () => {
  it('is used only after a reply failed to start, once, on the next tap', () => {
    const t = setup()
    t.output.prime() // silent primer that did not unlock the engine
    t.output.speak(['Reply.'], () => {}, () => {})
    t.timers[0]?.callback() // never started

    const before = t.spoken.length
    const notice = t.output.prime()

    assert.equal(notice, AUDIBLE_ACTIVATION_TEXT)
    assert.equal(t.spoken[before]?.text, AUDIBLE_ACTIVATION_TEXT)
    assert.equal(t.spoken[before]?.volume, 1) // this one is audible

    // A second failure does not repeat the spoken confirmation.
    t.output.speak(['Reply again.'], () => {}, () => {})
    t.timers[0]?.callback()
    assert.equal(t.output.prime(), null)
  })

  it('is never used when speech works', () => {
    const t = setup()
    t.output.prime()
    t.output.speak(['Reply.'], () => {}, () => {})
    t.spoken[1]?.onstart?.()
    t.spoken[1]?.onend?.()

    assert.equal(t.output.prime(), null)
    assert.ok(!t.spoken.some((u) => u.text === AUDIBLE_ACTIVATION_TEXT))
  })
})
