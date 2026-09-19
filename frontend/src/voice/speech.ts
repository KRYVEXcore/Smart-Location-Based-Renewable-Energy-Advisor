// Pure helpers for the voice layer. No DOM access, so they run under `node --test`.

// English only for now. A language picker can pass its own code to the same places later.
export const VOICE_LANGUAGE = 'en-IN'

// Model replies are plain text with the occasional **bold**, bullet or heading. Text
// to speech would read those markers aloud, so drop them before speaking.
export function stripMarkdownForSpeech(text: string): string {
  return text
    .replace(/[*#`]/g, '')
    .replace(/^\s*[-•]\s+/gm, '')
    .replace(/[ \t]+/g, ' ')
    .replace(/\s*\n\s*/g, '\n')
    .trim()
}

// Speech engines stop mid-way through very long utterances (Chrome around 15 s), so a
// reply is spoken as a queue of sentence-sized chunks. Cancelling clears the queue.
export function splitForSpeech(text: string, maxChars = 220): string[] {
  const sentences = text
    .split(/(?<=[.!?])\s+|\n+/)
    .map((part) => part.trim())
    .filter(Boolean)
  const chunks: string[] = []
  for (const sentence of sentences) {
    const last = chunks[chunks.length - 1]
    if (last !== undefined && last.length + 1 + sentence.length <= maxChars) chunks[chunks.length - 1] = `${last} ${sentence}`
    else chunks.push(sentence)
  }
  return chunks
}

// Voices differ per device, so none is hard-coded: prefer English (India), then any English.
export function pickVoice<T extends { lang: string }>(voices: readonly T[], language = VOICE_LANGUAGE): T | undefined {
  const wanted = language.toLowerCase().replace('_', '-')
  const exact = voices.find((voice) => voice.lang.toLowerCase().replace('_', '-') === wanted)
  return exact ?? voices.find((voice) => voice.lang.toLowerCase().startsWith('en'))
}
